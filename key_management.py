from PIL import Image
from io import BytesIO
import boto3
import requests

AWS_ACCESS_KEY_ID = 'AKIAZI2LHFOPGHENAJN2'
AWS_SECRET_ACCESS_KEY = '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'
S3_BUCKET_NAME = 'images4957'
s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)


def genData(data):
    if isinstance(data, str):
        # list of binary codes
        # of given data
        newd = []
        for i in data:
            newd.append(format(ord(i), '08b'))
        return newd
    elif isinstance(data, bytes):
        return [format(byte, '08b') for byte in data]
    elif isinstance(data, int):
        return format(data, '08b')
    else:
        raise ValueError("Unsupported data type for encoding")


def modPix(pix, data):
    datalist = genData(data)
    lendata = len(datalist)
    imdata = iter(pix)
    for i in range(lendata):
        pix = [value for value in imdata.__next__()[:3] +
               imdata.__next__()[:3] +
               imdata.__next__()[:3]]
        for j in range(0, 8):
            if datalist[i][j] == '0' and pix[j] % 2 != 0:
                pix[j] -= 1
            elif datalist[i][j] == '1' and pix[j] % 2 == 0:
                if pix[j] != 0:
                    pix[j] -= 1
                else:
                    pix[j] += 1
        if i == lendata - 1:
            if pix[-1] % 2 == 0:
                if pix[-1] != 0:
                    pix[-1] -= 1
                else:
                    pix[-1] += 1
        else:
            if pix[-1] % 2 != 0:
                pix[-1] -= 1
        pix = tuple(pix)
        yield pix[0:3]
        yield pix[3:6]
        yield pix[6:9]


def encode_enc(newimg, data):
    w = newimg.size[0]
    (x, y) = (0, 0)
    for pixel in modPix(newimg.getdata(), data):
        newimg.putpixel((x, y), pixel)
        if x == w - 1:
            x = 0
            y += 1
        else:
            x += 1


# Encode data into image
def encode_from_url(url, data):
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError("Failed to download the image.")
    image = Image.open(BytesIO(response.content))
    newimg = image.copy()
    encode_enc(newimg, data)
    return newimg


# Decode the data from the image
def decode_image(image):
    data = ''
    imgdata = iter(image.getdata())
    while True:
        pixels = [value for value in imgdata.__next__()[:3] +
                  imgdata.__next__()[:3] +
                  imgdata.__next__()[:3]]
        binstr = ''
        for i in pixels[:8]:
            if i % 2 == 0:
                binstr += '0'
            else:
                binstr += '1'
        data += chr(int(binstr, 2))
        if pixels[-1] % 2 != 0:
            return data


def encode(url, data, s3_bucket_name, filename, folder_name):
    encoded_image = encode_from_url(url, data)
    filename = f"{folder_name}/{filename}"
    print(filename+'in encode image')
    with BytesIO() as image_buffer:
        encoded_image.save(image_buffer, format='PNG')  # Assuming PNG format
        image_buffer.seek(0)
        s3_client.upload_fileobj(image_buffer, s3_bucket_name, filename)


def get_Key(username, filename):
    filename = f"{username}/{filename}"
    print(filename+'in get key')
    s3_object = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=filename)
    image_data = s3_object['Body'].read()
    retrieved_image = Image.open(BytesIO(image_data))

    decoded_data = decode_image(retrieved_image)
    return decoded_data
