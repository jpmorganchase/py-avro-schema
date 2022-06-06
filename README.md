# py-avro-schema

Generate Apache Avro schemas for Python types.

## Installing

```shell
python -m pip install py-avro-schema
```

## Developing

To setup a scratch/development virtual environment (under `.venv/`), first install [Tox](https://pypi.org/project/tox/).
Then run:

```shell
tox -e dev
```

The `py-avro-schema` package is installed in
[editable mode](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs) inside the `.venv/` environment.

Run tests by simply calling `tox`.

Install code quality Git hooks using `pre-commit install --install-hooks`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)
