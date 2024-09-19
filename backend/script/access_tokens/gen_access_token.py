import uuid


def gen_access_token():
    token = f'{uuid.uuid4()}'.replace("-", "").upper()
    return token


if __name__ == "__main__":
    for i in range(20):
        token = gen_access_token()
        print("i={} - token={}".format(i, token))
