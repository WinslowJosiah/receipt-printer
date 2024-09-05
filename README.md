# receipt-printer

My shenanigans with a receipt printer.

Requires [python-escpos](https://python-escpos.readthedocs.io/). To install it, run this in your terminal:

```bash
pip install python-escpos
```

## Purpose

On August 18th, 2024, [I got a receipt printer](https://winslowjosiah.com/blog/2024/08/27/i-got-a-receipt-printer/), and I decided to write programs to make it print things. I chose to write them in Python because it was the most frictionless option to me at the time (although I have an experiment in the works for a version of this in JavaScript...stay tuned!).

These programs work as-is on both my Windows 11 laptop and my Android phone (with Pydroid 3; even though I can't figure out how to connect to Bluetooth with Pydroid 3, printing to files still works). To get them to work with your printer, you'll have to change the `printer\get_printer.py` file, and replace my printer's profile and MAC address with your own. (This has only been tested on my own printer.)

If these programs don't work for you (even after the necessary modifications), let me know, and I'll try to troubleshoot.

## Files

* `hawktalon.py`

One of my first demos, based on [a tweet from a friend](https://twitter.com/HawktalonDraws/status/1655717080379916289) which seems to apply here.

* `weather.py`

Your location is gathered as input. Output is a weather summary for today, a weather forecast for the next week, and any currently active weather alerts if applicable.

(NOTE: Make sure you have a valid `OPENCAGE_API_KEY` and `VISUALCROSSING_API_KEY` defined in `.env`!)

* `album.py`

Input a [MusicBrainz](https://musicbrainz.org/) _release_ ID (only works with releases!). Output is the information for that release.

---

I also have a file called `printbin.bat`, which prints a file to my printer as raw binary data, either by Bluetooth or by USB controlled with the `Win32Raw` printer class (whichever is available). This is useful for when I've printed to a file, and not my printer for whatever reason.
