# Transpilation outputs v2.0

| Target | Usage | Implementation status | 
| :--- | :--- | :--- | 
| Mermaid | diagrammatic representation *(mindmap, flowchart)* | ![](https://img.shields.io/badge/status-up-brightgreen) |
| Alloy | formal verification | ![](https://img.shields.io/badge/status-up-brightgreen) |
| JSON | REST APIs | ![](https://img.shields.io/badge/status-not%20implemented-ff3333) |
| Catala | decision logic | ![](https://img.shields.io/badge/status-not%20implemented-ff3333) |
| R | data modelling and visualisation | ![](https://img.shields.io/badge/status-not%20implemented-ff3333) |

## Usage 

### 1. Transpile `.yh` to `.mmd`

```console
$ racket to_mmd/trans_mmd_mindmap.rkt
$ racket to_mmd/trans_mmd_flowchart.rkt
```

* Read `.yh` files are in `./check/dep/yh`
* Valid `.mmd` files are in `./check/dep/mmd_*`
* Transpiled `.mmd` files are in `./check/out/mmd_*`

### 2. Transpile `.yh` to `.als`

```console
$ racket to_als/trans_als.rkt
```

* Read `.yh` files are in `./check/dep/yh`
* Valid `.als` files are in `./check/dep/als`
* Transpiled `.als` files are in `./check/out/als`

### 3. Validate transpilation outputs 

```console
$ racket check/validate.rkt
```
