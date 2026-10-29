"""Shared DAG mesh-channel encoding, including three-component map channels."""
from .constants import DAG_OBJ_BIGMESH, DAG_OBJ_MESH, NUMMESHTCH


def write_mesh_data(writer, mesh):
    channels = []
    if mesh.color_attributes:
        channels.append((0, 3, [tuple(value[:3]) for value in mesh.color_attributes], mesh.color_attributes_poly))
    for index, values in enumerate(mesh.uv):
        if values and index + 1 not in mesh.map_channels:
            dimensions = 3 if index == 0 else 2
            points = [tuple(value) + ((0,) if dimensions == 3 else ()) for value in values]
            channels.append((index + 1, dimensions, points, mesh.uv_poly[index]))
    for channel, (points, indices) in mesh.map_channels.items():
        channels.append((channel, 3, points, indices))
    channels.sort(key=lambda channel: channel[0])
    maximum = max((len(channel[2]) for channel in channels), default=0)
    big = max(len(mesh.vertices), len(mesh.faces), maximum) >= 65536
    chunk = writer.beginChunk(DAG_OBJ_BIGMESH if big else DAG_OBJ_MESH)
    write_count = writer.writeDWord if big else writer.writeUShort
    write_face = writer.writeBigFace if big else writer.writeFace
    write_count(len(mesh.vertices))
    for vertex in mesh.vertices:
        writer.writeVertex(vertex)
    write_count(len(mesh.faces))
    for face in mesh.faces:
        write_face(face.f, face.smgr, face.mat)
    writer.writeByte(len(channels))
    for channel, dimensions, points, indices in channels:
        if len(indices) != len(mesh.faces) * 3:
            raise ValueError(f'DAG map channel {channel} has incomplete face indices')
        write_count(len(points))
        writer.writeByte(dimensions)
        writer.writeByte(channel)
        for point in points:
            for component in point:
                writer.writeFloat(component)
        for index in indices:
            write_count(index)
    writer.endChunk(chunk)


def read_mesh_channels(reader, mesh, face_count, big=False):
    read_count = reader.readDWord if big else reader.readUShort
    channel_count = reader.readByte()
    for _ in range(channel_count):
        count, dimensions, channel = read_count(), reader.readByte(), reader.readByte()
        if dimensions not in (1, 2, 3):
            raise ValueError(f'Invalid DAG map dimensions: {dimensions}')
        points = [tuple(reader.readFloat() for _ in range(dimensions)) for _ in range(count)]
        indices = []
        for _ in range(face_count):
            a, b, c = read_count(), read_count(), read_count()
            indices.extend((a, c, b))
        if any(index >= count for index in indices):
            raise ValueError(f'DAG map channel {channel} references missing vertices')
        points = [point + (0,) * (3 - dimensions) for point in points]
        if channel == 0:
            mesh.color_attributes = points
            mesh.color_attributes_poly = indices
        elif 1 <= channel <= NUMMESHTCH:
            if dimensions == 3 and (channel == 8 or any(point[2] != 0 for point in points)) or channel > 8:
                mesh.map_channels[channel] = (points, indices)
            if channel <= 8:
                mesh.uv.extend([] for _ in range(len(mesh.uv), channel))
                mesh.uv_poly.extend([] for _ in range(len(mesh.uv_poly), channel))
                mesh.uv[channel - 1] = [value for point in points for value in point[:2]]
                mesh.uv_poly[channel - 1] = indices
