# SDK Quickstart

## Python

```python
from yuho.services.analysis import analyze_source
from yuho.transpile import TranspileTarget
from yuho.transpile.registry import TranspilerRegistry

result = analyze_source('statute 1 "Test" { elements { actus_reus act := "Did something"; } }')
transpiler = TranspilerRegistry.instance().get(TranspileTarget.ENGLISH)
print(transpiler.transpile(result.ast))
```

## TypeScript

```bash
npm install @yuho/sdk
```

```typescript
import { YuhoClient } from '@yuho/sdk';

const yuho = new YuhoClient({ baseUrl: 'http://localhost:8080' });
const result = await yuho.parse('statute 1 "Test" { ... }');
console.log(result.data);
```

## Go

```bash
go get github.com/gongahkia/yuho-go
```

```go
import "github.com/gongahkia/yuho-go"

client := yuho.NewClient(yuho.Config{BaseURL: "http://localhost:8080"})
resp, err := client.Parse(ctx, `statute 1 "Test" { ... }`)
```

## Java

```java
var client = new dev.yuho.YuhoClient("http://localhost:8080");
String result = client.parse("statute 1 \"Test\" { ... }");
```

## REST (curl)

```bash
# start server
yuho api --port 8080

# parse
curl -X POST http://localhost:8080/v1/parse \
  -H "Content-Type: application/json" \
  -d '{"source": "statute 1 \"Test\" { ... }"}'

# transpile
curl -X POST http://localhost:8080/v1/transpile \
  -H "Content-Type: application/json" \
  -d '{"source": "...", "target": "english"}'
```
