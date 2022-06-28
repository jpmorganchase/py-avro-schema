# py-avro-schema

Generate Apache Avro schemas for Python types including standard library data-classes and Pydantic data models.

Documentation: https://py-avro-schema.readthedocs.io/


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

## Terms & Conditions

Copyright 2022 J.P. Morgan Chase & Co.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.


## Contributing

See [CONTRIBUTING.md](https://github.com/jpmorganchase/.github/blob/main/CONTRIBUTING.md)
