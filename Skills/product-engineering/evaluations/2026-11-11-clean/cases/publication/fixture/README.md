# Local report packages

Python 3.11+, standard library only. Run:

```sh
python3 -m unittest discover -s tests -v
```

`artifact_bundle` publishes a set of related report files. `report_view` reads
heading and detail from the same package; it also accepts a retained reader for
a preview that stays open while newer reports are published. Publication means
changing what a *new* reader sees, after the whole candidate has been accepted.
See CONTRACT.md for source, persistence and error guarantees.

Stable API, all in `artifact_bundle.py`:

- `PackageError(RuntimeError)`: invalid/unreadable published package.
- `publish(root, files, *, validate=None) -> str`: new opaque release ID.
- `open_package(root) -> PackageReader | None`: read the active pointer once.
- `PackageReader.release_id: str`, `names: tuple[str, ...]` (sorted),
  `read(name) -> bytes`. Construct readers through open_package or validation;
  the class's initializer is private and may change. No close method is needed:
  readers do not require callers to retain an open handle.

`report_view.render(reader) -> str` combines summary.json's `title` with a newline
and UTF-8 detail.txt. `current_report(root) -> str | None` opens one reader and
renders it. Its JSON/title/text errors belong to the consumer; the publisher's
optional validator is where an application can reject unsuitable report content.

This is a disposable read artifact, not the original report source. Existing
valid packages and readers must remain usable without republishing or migrating.
The on-disk protocol is stable; private staging organization may change.
