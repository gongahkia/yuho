# Transpilers `.yh` to `.mmd`

Source code can also be found here.

* [`yuho_to_json`](../../src/secondary/yuho_to_json)
* [`json_to_mmd`](../../src/secondary/json_to_mmd)

Also, see the below.

* [json.org](https://www.json.org/json-en.html)
* [mermaid.js.org](https://mermaid.js.org/)

## Usage  

### 1. Transpile `.yh` to `.json`

```console
$ python<versionNumber> trans_json.py
```

* Read `.yh` files are in `./web/dep/yh`.
* Transpiled `.json` files are in `./web/out/json`.
* Valid `.json` files are in `./web/dep/json`.

### 2. Transpile `.json` to `.mmd`

```console
$ python<versionNumber> trans_mmd.py
```

* Read `.json` files are in `./web/out/json`.
* Transpiled `.mmd` files are in `./web/out/mmd`.
* Valid `.mmd` files are in `./web/dep/mmd`.

### 3. Validation

```console
$ python<versionNumber> validate.py
```