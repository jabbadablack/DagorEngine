"""Packed DagLight/DagLight2 layout from maxplug/dagfmt.h.

Max intensity is mapped numerically to Blender energy. This preserves the DAG
multiplier; it does not imply matching photometric units between renderers.
"""
import math
import struct
from dataclasses import dataclass


LEGACY = struct.Struct('<5fB')
EXTENDED = struct.Struct('<B3f')
LIGHT_TYPES = ('POINT', 'SPOT', 'SUN')


@dataclass
class DagLight:
    color: tuple
    range: float
    decay_radius: float
    decay: int
    type: int = 0
    hotspot: float = 0.0
    falloff: float = 0.0
    intensity: float = 1.0

    @classmethod
    def from_bytes(cls, data):
        if len(data) not in (LEGACY.size, LEGACY.size + EXTENDED.size):
            raise ValueError(f'Unsupported DAG light payload size: {len(data)}')
        r, g, b, distance, radius, decay = LEGACY.unpack_from(data)
        if len(data) == LEGACY.size:
            # Same fallback as the Max importer for pre-DagLight2 files.
            return cls((r, g, b), distance, radius, decay, intensity=max(r, g, b))
        kind, hotspot, falloff, intensity = EXTENDED.unpack_from(data, LEGACY.size)
        if kind >= len(LIGHT_TYPES):
            raise ValueError(f'Unsupported DAG light type: {kind}')
        return cls((r, g, b), distance, radius, decay, kind, hotspot, falloff, intensity)

    def to_bytes(self):
        return (LEGACY.pack(*self.color, self.range, self.decay_radius, self.decay)
                + EXTENDED.pack(self.type, self.hotspot, self.falloff, self.intensity))

    @classmethod
    def from_blender(cls, light):
        if light.type not in LIGHT_TYPES:
            raise ValueError(f'{light.name}: DAG supports Point, Spot and Sun lights; got {light.type}')
        falloff = math.degrees(light.spot_size) if light.type == 'SPOT' else 0.0
        hotspot = falloff * (1.0 - light.spot_blend) if light.type == 'SPOT' else 0.0
        result = cls(tuple(c * light.energy for c in light.color),
                   light.cutoff_distance if light.use_custom_distance else 0.0,
                   light.get('dagor_decay_radius', 0.0), light.get('dagor_decay', 2),
                   LIGHT_TYPES.index(light.type), hotspot, falloff, light.energy)
        payload = light.get('_dagor_light_payload')
        preview = light.get('_dagor_light_preview')
        if payload and preview is not None and len(preview) == 9:
            original = cls.from_bytes(bytes.fromhex(payload))
            current = cls.preview_values(light)
            # Native Blender fields clamp some values that the Max format
            # permits. Preserve those values when the corresponding preview
            # controls have not been edited (including transform-only edits).
            def unchanged(indices):
                return all(abs(current[index] - preview[index]) < 1e-7 for index in indices)
            if unchanged(range(4)):
                result.color, result.intensity = original.color, original.intensity
            if unchanged((4, 5)):
                result.range = original.range
            if unchanged((6, 7, 8)):
                result.hotspot, result.falloff = original.hotspot, original.falloff
        return result

    @staticmethod
    def preview_values(light):
        return [light.energy, *light.color, float(light.use_custom_distance), light.cutoff_distance,
                light.spot_size if light.type == 'SPOT' else 0.0,
                light.spot_blend if light.type == 'SPOT' else 0.0, float(LIGHT_TYPES.index(light.type))]

    def apply_to_blender(self, light):
        light.energy = self.intensity
        divisor = self.intensity if self.intensity != 0 else 1.0
        light.color = tuple(c / divisor for c in self.color)
        light.use_custom_distance = self.range > 0
        if self.range > 0:
            light.cutoff_distance = self.range
        # Blender has no matching Max decay model. Retain these as custom
        # properties, available in Light Data > Custom Properties, for export.
        light['dagor_decay_radius'] = self.decay_radius
        light['dagor_decay'] = self.decay
        if light.type == 'SPOT':
            light.spot_size = math.radians(self.falloff)
            light.spot_blend = 1.0 - self.hotspot / self.falloff if self.falloff else 0.0
        light['_dagor_light_payload'] = self.to_bytes().hex()
        light['_dagor_light_preview'] = self.preview_values(light)
