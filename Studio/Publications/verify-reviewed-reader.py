from pathlib import Path, PurePosixPath
import hashlib,json
root=Path("Reader")
release=json.loads(Path("Studio/Publications/reviewed-reader-53-2026-10-31.json").read_text())
marker=(root/".generated-reader.json").read_bytes()
assert hashlib.sha256(marker).hexdigest()==release["marker_sha256"]
files=json.loads(marker)["files"]
actual={p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
assert actual==set(files)|{".generated-reader.json"}
assert not any(p.is_symlink() for p in root.rglob("*"))
total=len(marker)
for name,digest in files.items():
 p=PurePosixPath(name)
 assert not p.is_absolute() and ".." not in p.parts
 body=(root/name).read_bytes()
 assert hashlib.sha256(body).hexdigest()==digest,name
 total+=len(body)
assert len(actual)==release["reader_files"] and total==release["reader_bytes"]
assert len(list((root/"stories").glob("*.html")))==73
print("PASS: exact reviewed snapshot:",len(actual),"files,",total,"bytes; 53 revised primaries + 3 alternatives; 17 prior versions")
