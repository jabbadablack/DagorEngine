"""Typed, flat BLK object scripts with quoting and Dagor tilde escapes."""
import math
import re


TYPES = {'t', 'b', 'i', 'r', 'p2', 'p3', 'p4', 'ip2', 'ip3', 'm'}


def statements(text):
    buffer, quote, depth, index = [], None, 0, 0
    while index < len(text):
        char = text[index]
        if quote:
            buffer.append(char)
            if char == '~' and index + 1 < len(text):
                index += 1
                buffer.append(text[index])
            elif char == quote:
                quote = None
        elif char in '\"\'':
            quote = char
            buffer.append(char)
        elif char == '/' and text[index:index + 2] == '//':
            while index < len(text) and text[index] not in '\r\n':
                index += 1
            continue
        elif char in '[(':
            depth += 1
            buffer.append(char)
        elif char in '])':
            depth -= 1
            buffer.append(char)
        elif char in ';\r\n' and depth == 0:
            if ''.join(buffer).strip():
                yield ''.join(buffer).strip()
            buffer = []
        else:
            buffer.append(char)
        index += 1
    if ''.join(buffer).strip():
        yield ''.join(buffer).strip()


def unquote(value):
    if not value or value[0] not in '\"\'':
        return value
    if len(value) < 2 or value[-1] != value[0]:
        raise ValueError('Unterminated object-property string')
    text, output, index = value[1:-1], [], 0
    escapes = {'n': '\n', 'r': '\r', 't': '\t', '~': '~', '"': '"', "'": "'"}
    while index < len(text):
        char = text[index]
        if char == '~' and index + 1 < len(text):
            index += 1
            char = escapes.get(text[index], text[index])
        output.append(char)
        index += 1
    return ''.join(output)


def quote(value):
    return '"' + str(value).replace('~', '~~').replace('"', '~"').replace('\r', '~r').replace('\n', '~n').replace('\t', '~t') + '"'


def as_bool(value):
    if isinstance(value, str):
        if value.lower() in {'yes', 'true', '1'}:
            return True
        if value.lower() in {'no', 'false', '0'}:
            return False
        raise ValueError(f'Invalid boolean: {value}')
    return bool(value)


def parse_value(kind, value):
    if kind == 't':
        return unquote(value)
    if kind == 'b':
        return as_bool(value)
    if kind == 'i':
        return int(value)
    if kind == 'r':
        result = float(value)
        if not math.isfinite(result):
            raise ValueError('Non-finite real property')
        return result
    expected = 12 if kind == 'm' else int(kind[-1])
    tokens = [token for token in re.split(r'[\s,\[\]]+', value) if token]
    if len(tokens) != expected:
        raise ValueError(f'{kind} requires {expected} components')
    result = [int(token) if kind.startswith('ip') else float(token) for token in tokens]
    if not all(math.isfinite(number) for number in result):
        raise ValueError('Non-finite vector property')
    return result


def parse_properties(text):
    result, broken = {}, []
    for statement in statements(text):
        match = re.fullmatch(r'([^:=\r\n]+):([a-z0-9]+)\s*=\s*(.*)', statement, re.DOTALL)
        if not match:
            broken.append(statement)
            continue
        name, kind, value = match.groups()
        if kind not in TYPES:
            broken.append(statement)
            continue
        try:
            result[name.strip() + ':' + kind] = parse_value(kind, value.strip())
        except ValueError:
            broken.append(statement)
    if broken:
        previous = result.get('broken_properties:t', '')
        result['broken_properties:t'] = ';'.join(filter(None, [previous, *broken]))
    return result


def serialize_properties(properties):
    lines, broken = [], []
    for key, value in properties.items():
        if key == 'broken_properties:t':
            broken.append(str(value))
            continue
        try:
            name, kind = key.rsplit(':', 1)
            if kind not in TYPES or not name:
                raise ValueError('Invalid property name/type')
            if kind == 't':
                encoded = quote(value)
            elif kind == 'b':
                encoded = 'yes' if as_bool(value) else 'no'
            elif kind in {'i', 'r'}:
                encoded = str(parse_value(kind, str(value)))
            else:
                values = value.to_list() if hasattr(value, 'to_list') else list(value)
                parsed = parse_value(kind, ','.join(map(str, values)))
                if kind == 'm':
                    encoded = '[' + ' '.join('[' + ', '.join(map(str, parsed[i:i + 3])) + ']'
                                              for i in range(0, 12, 3)) + ']'
                else:
                    encoded = ', '.join(map(str, parsed))
            lines.append(f'{name}:{kind}={encoded}')
        except (ValueError, TypeError):
            broken.append(f'{key}={value}')
    if broken:
        # Preserve malformed legacy data instead of silently dropping it.
        lines.append('broken_properties:t=' + quote(';'.join(broken)))
    return '\r\n'.join(lines)
