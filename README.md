# Sprint 05 - Хувийн туслах AI агент
23B1NUM1041 · П.Дөлгөөн

Week 3 SRS болон Week 4 ADR-003-д тулгуурласан API гэрээ, ажилладаг локал sandbox, тусдаа Corg.ly UE-5 дасгал.
Энэ нь production AI/Google интеграци биш. Sandbox нь Google рүү хүсэлт илгээхгүй, JWT/OAuth шалгахгүй,
тогтмол sandbox bearer token хэрэглэнэ. Төлөв зөвхөн санах ойд байна; restart хийхэд арилна.

## Ажиллуулах
Python 3.11+ шаардлагатай. Python нэмэлт package шаардахгүй.

```sh
python server.py
```

http://127.0.0.1:8080/swagger/ - Swagger UI; http://127.0.0.1:8080/redoc.html - Redoc.
Swagger-д Authorize товчоор `sprint05-local-sandbox` оруулна (Bearer угтвар оруулахгүй).
Assistant болон Corg.ly spec-ийг Swagger-ийн дээд жагсаалтаас сонгоно.
Тусдаа Corg.ly Redoc: http://127.0.0.1:8080/corgly-redoc.html.

Өөр terminal дээр доорх sample бүрийг ажиллуулна. Assets-ийн зам script-ийн байрлалаас шийдэгдэнэ.

```sh
python samples/assistant_workflow.py
python samples/upload_photo.py
python samples/translate_bark.py
python samples/subscribe_webhook.py
```

Sample бүр actual HTTP response-ийг status ба JSON-тай хэвлэнэ. Local fixtures: жижиг PNG болон синтетик WAV;
жинхэнэ нохойн зураг/хуцалт биш. Callback нь documentation example domain; sandbox зөвхөн бүртгэж,
ямар ч callback URL руу холбогдохгүй. Нууц token, бодит хувийн өгөгдөл оруулах шаардлагагүй.

## Шалгалт ба docs build
Node.js 22.12+ ашиглана. Эхний команд package lock-д түгжсэн хэрэгслүүдийг суулгана.

```sh
npm ci
npm run lint
npm run build
python -m unittest discover -s tests -v
```

`evidence/` дотор бодитоор ажиллуулсан HTTP sample payload, test log, lint log бий.
`docs/decision-report.md` нь яг 100 үгтэй англи харьцуулалт; Монгол тайлбар PDF-д бий.

## Гэрээний хүрээ
Assistant-ийн 5 POST path нь /v1 суурь хаягтай. Read operation-ууд болох /contacts/search,
/sessions/history нь энэ lab-д JSON filter body бүхий POST хэлбэртэй; read-only, side effect үгүй.
Энэ нь бүх endpoint-д requestBody шаардсан rubric-т нийцсэн шийдвэр.
Week 4-ийн /commands, /actions/{id}/confirm, /actions/{id}/execute урсгалыг хадгалсан.
History: B26 нь B25-ийн session-scoped records-ийг API-аар гаргана; B1 history UI болон production DB үлдсэн.
Command sandbox зөвхөн бүтэцтэй Calendar санал хүлээн авна. STT, intent AI, Gmail, OAuth consent,
PostgreSQL, cancellation UI хэрэгжээгүй. Эдгээрийг бүрэн болсон гэж тайлагнаагүй.

## Public deployment ба repository
Public URL болон repository commit энэ багцаас автоматаар үүсэхгүй. `DEPLOYMENT.md`-г дагана.
`public/` нь шууд байршуулж болох docs; интерактив public sandbox-д Python service бас хэрэгтэй.
