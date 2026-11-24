"""Small curve used ONLY to verify the arithmetic example in the report.

Not imported by the signing application. Not suitable for protecting data.
"""
P, A, B, N = 17, 2, 2, 19
G = (5, 1)


def add(left, right):
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    slope = ((3 * x1 * x1 + A) * pow(2 * y1, -1, P) if left == right
             else (y2 - y1) * pow(x2 - x1, -1, P)) % P
    x3 = (slope * slope - x1 - x2) % P
    return x3, (slope * (x1 - x3) - y1) % P


def multiply(scalar, point=G):
    if scalar < 0:
        raise ValueError("Use a nonnegative scalar in the teaching example")
    result = None
    while scalar:
        if scalar & 1:
            result = add(result, point)
        point = add(point, point)
        scalar >>= 1
    return result


def worked_example():
    private, nonce, z = 7, 3, 13
    public = multiply(private)
    r = multiply(nonce)[0] % N
    s = (pow(nonce, -1, N) * (z + r * private)) % N
    w = pow(s, -1, N)
    u1, u2 = (z * w) % N, (r * w) % N
    point = add(multiply(u1), multiply(u2, public))
    return {"Q": public, "r": r, "s": s, "w": w, "u1": u1, "u2": u2, "X": point}
