import requests

from PIL import Image

from utils import get_printer


p = get_printer(__file__)
p.hw("INIT")

p.set(bold=True)
p.text("Hawktalon")
p.set(bold=False)
p.text(" @HawktalonDraws")
p.ln(2)

p.block_text("I DONT NEED MORE TECH I DONT NEED TO SPEND A THOUSAND DORLARS I DONT NEED MORE TECH I DONT NEED TO SPEND A THOUSAND DORLARS I DONT NEED MORE TECH I DONT NEED TO SPEND A THOUSAND DORLARS")
p.ln(2)

url = "https://pbs.twimg.com/media/FvpJ6RyWYAcG-Zu?format=jpg&name=large"
img = Image.open(requests.get(url, stream=True).raw)

width = p.profile.profile_data["media"]["width"]["pixels"]
height = int(width * img.height / img.width)
img = img.resize((width, height), Image.LANCZOS)
p.image(img, center=True)
p.ln(2)

p.text("6:31 PM - May 8, 2023")
p.ln(2)

p.ln(4)
