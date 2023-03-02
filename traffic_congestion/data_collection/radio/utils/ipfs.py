from ipyfs import Files

files = Files(host="http://11.11.1.89", port=5001)

with open("text.txt", "rb") as f:
    files.write(path=f"/{f.name}", file=f, create=True)
