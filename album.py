import requests
from requests.exceptions import RequestException

from PIL import Image
from unidecode import unidecode

from utils import get_printer


# Get release information
mbid = input("Enter MusicBrainz ID for release: ")
try:
    r = requests.get(
        f"https://musicbrainz.org/ws/2/release/{mbid}",
        params={
            "inc": "artist-credits+genres+labels+recordings+release-groups",
            "fmt": "json",
        },
        headers={
            "User-Agent": "AlbumPrinter/0.0.1 ( winslowjosiah@gmail.com )",
        },
    )
    r.raise_for_status()
except RequestException as e:
    print("Error getting album info!")
    raise SystemExit(e)
release = r.json()


# Get album art
album_art = None
url = f"http://coverartarchive.org/release/{mbid}/front"
try:
    r = requests.get(url, stream=True)
    r.raise_for_status()
    album_art = Image.open(r.raw)
except RequestException as e:
    print("Error getting album front cover art!")
    print(e)

    url = f"http://coverartarchive.org/release/{mbid}"
    try:
        r = requests.get(url)
        r.raise_for_status()

        images = r.json()["images"]
        if images:
            # HACK We're just getting the first image, whatever it is.
            url = images[0]["image"]
            try:
                r = requests.get(url, stream=True)
                r.raise_for_status()
                album_art = Image.open(r.raw)
            except RequestException as e:
                print("Error getting any album cover art!")
                print(e)
    except RequestException as e:
        print("Error getting list of album cover art!")
        print(e)


# Initialize printer
p = get_printer(__file__)
media_width = p.profile.profile_data["media"]["width"]["pixels"]
font_0_columns = p.profile.profile_data["fonts"]["0"]["columns"]
p.hw("INIT")
p.ln(3)

# Title / artist
artist_id = release["artist-credit"][0]["artist"]["id"]
p.set(double_width=True, double_height=True, align="center")
p.block_text(
    unidecode(release["title"]),
    columns=font_0_columns // 2,
)
p.ln()
p.set(normal_textsize=True, align="center")
artists = ""
for artist in release["artist-credit"]:
    artists += artist["name"] + artist["joinphrase"]
p.block_text(unidecode(artists))
p.ln()
p.set(align="left")
p.ln()

# Album art
if album_art is not None:
    height = int(media_width * album_art.height / album_art.width)
    album_art = album_art.resize((media_width, height), Image.LANCZOS)
    p.image(album_art, center=True)
    p.ln(2)

# Calculate tracklist column widths / alignments
number_column_width = 2
padding_column_width = 1
length_column_width = 6
title_column_width = (
    font_0_columns
    - number_column_width - padding_column_width - length_column_width
)
column_widths = [
    number_column_width, padding_column_width, title_column_width,
    length_column_width,
]
column_aligns = ["right", "left", "left", "right"]

# Tracklist
p.set(double_width=True, align="center")
p.textln("Tracklist")
p.set(normal_textsize=True, align="left")
p.ln()
for media in release["media"]:
    media_title = media["title"]
    if media_title:
        p.set(double_height=True)
        p.block_text(unidecode(media_title))
        p.set(normal_textsize=True)
        p.ln(2)

    # Tracklist header
    p.set(bold=True)
    p.software_columns(
        ["#", "", "TITLE", "LENGTH"],
        column_widths,
        column_aligns,
    )
    p.textln("-" * font_0_columns)
    p.set(bold=False)

    tracks = media["tracks"]
    unknown_length = False
    for track in tracks:
        track_length = track.get("length", None)
        if track_length is None:
            track_length_str = "?:??"
            unknown_length = True
        else:
            minutes, seconds = divmod(track_length // 1000, 60)
            track_length_str = f"{minutes}:{seconds:02}"

        track_title = track["recording"]["title"]
        # Add other artists to title, if any
        if any(
            artist["artist"]["id"] != artist_id
            for artist in track["artist-credit"]
        ):
            track_artists = ""
            for artist in track["artist-credit"]:
                track_artists += artist["name"] + artist["joinphrase"]
            track_title += f"\n({track_artists})"

        row = [track["number"], "", unidecode(track_title), track_length_str]
        p.software_columns(
            row, column_widths, column_aligns, break_long_words=True,
        )
        p.textln("-" * font_0_columns)

    # Full length
    if not unknown_length:
        full_length = sum(
            track["length"]
            for track in tracks
        ) // 1000
        full_minutes, full_seconds = divmod(full_length, 60)
        full_hours, full_minutes = divmod(full_minutes, 60)
        if full_hours:
            full_length_parts = (full_hours, full_minutes, full_seconds)
        else:
            full_length_parts = (full_minutes, full_seconds)
        p.set(bold=True, align="right")
        p.textln(
            ":".join(
                f"{part:02}"
                for part in full_length_parts
            ).lstrip("0")
        )
        p.set(bold=False, align="left")
    p.ln()

# Release information
p.set(double_width=True, align="center")
p.textln("Release Info")
p.set(normal_textsize=True, align="left")
p.ln()

# Release date
release_date = release["release-events"][0]["date"]
if release_date:
    p.block_text(f"Released: {release_date}")
    p.ln()

# Release country
area = release["release-events"][0]["area"]
if area is not None:
    p.block_text(f"Country: {area['name']}")
    p.ln()

# Release format
release_format = release["media"][0]["format"]
if release_format is not None:
    p.block_text(f"Format: {release_format}")
    p.ln()

# Release genre
genres = sorted(
    release["release-group"]["genres"],
    key=lambda g: (-g["count"], g["name"])
)
if genres:
    genres_str = ", ".join(genre["name"] for genre in genres[:5])
    p.block_text(f"Genre: {genres_str}")
    p.ln()

# Release label
label_info = release["label-info"]
if label_info:
    labels = []
    seen_labels = set()
    for label in label_info:
        if label["label"]["id"] in seen_labels:
            continue
        seen_labels.add(label["label"]["id"])
        labels.append(label["label"]["name"])
    p.block_text(f"Label: {'; '.join(map(unidecode, labels))}")
    p.ln()

# Release status
status = release["status"]
if status is not None:
    p.block_text(f"Status: {status}")
    p.ln()

# UPC-A barcode
if release["barcode"] is not None:
    p.ln()
    p.barcode(release["barcode"], "UPCA")
    p.ln()

# Padding
p.ln(6)
