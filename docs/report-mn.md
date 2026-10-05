SPRINT 05  /  01

OpenAPI 3.0 ба
кодын жишээний аудит




**ПРОГРАММ ХАНГАМЖИЙН ТӨСЛИЙН БАРИМТ БИЧИГ**

Week 05 - Гэрийн даалгавар<br/>Үндсэн төсөл: Хувийн туслах AI агент<br/>23B1NUM1041 · П.Дөлгөөн<br/>2026-10-05

Зорилго ба үр дүн

Week 3-ын SRS v1.0, Week 4-ийн ADR-003-д тодорхойлсон command → confirmation → execution урсгалыг OpenAPI 3.0.3 гэрээ болголоо. Үндсэн төсөлд 5 endpoint, Corg.ly UE-5 дасгалд тусдаа 3 endpoint, ажилладаг Python жишээ, аудит болон хоёр renderer-ийн эхийг бэлтгэв.

| Хүргэлт | Нотолгоо |
| --- | --- |
| Assistant API: 5 endpoint | docs/openapi/openapi.yaml; бүх operation-д request/response example, security, schema бий. |
| Corg.ly UE-5: 3 Python sample | Зураг upload, bark translation, webhook subscription; actual mock HTTP response хадгалсан. |
| Чанарын шалгалт | Хоёр YAML: Redocly CLI 2.58.0 validation амжилттай. 12 HTTP integration test амжилттай. |
| Хоёр renderer | Swagger UI ба Redoc локал browser-д дүрслэгдсэн; build хийсэн HTML багцад орсон. |
| Хязгаар | Public deployment, remote commit, GitHub CI run хийгдээгүй. Hosting/repository өгөөгүй. |

Нотолгооны хил

Sandbox нь бодит HTTP сервер боловч provider-ийн үр дүнг загварчилна. Google OAuth, бодит Calendar/Gmail write, STT/intent модель, PostgreSQL болон webhook delivery хэрэгжээгүй. Энэ багц нь API contract ба sample-ийн лабораторийн нотолгоо; production системийн баталгаа биш.

SPRINT 05  /  02

Үндсэн API ба мөрдөлт




Base URL: **http://127.0.0.1:8080/v1**. Доорх таван path бүгд POST method, JSON request body, 200 response болон 4xx/5xx тодорхойлолттой. Хоёр read operation JSON filter авах тул POST ашигласан; provider-д бичих үйлдэл хийхгүй.

| Path | Оролт → гаралт | W3 / W4 холбоос |
| --- | --- | --- |
| /commands | session_id, transcript, intent, event → action_id, version, review payload | FR-03/04; B21. Sandbox нь бэлэн бүтэцтэй Calendar intent авна. |
| /actions/{id}/confirm | session_id, payload_version → confirmed | FR-05/10; B22/B25. Payload version зөрвөл 409. |
| /actions/{id}/execute | session_id, payload_version → status, provider_resource_id | FR-07/13; B23/B25. Зөвхөн confirmed action. |
| /contacts/search | query → contacts[name,email] | FR-08/12; B23. Зөвхөн fixture contact хайна. |
| /sessions/history | session_id → items[action,type,status,time] | FR-15; шинээр B26 + B25. History UI B1-д үлдсэн. |

Week 4-ийн orphan шаардлагын шийдэл

FR-15-ын API эзнийг B26 Session History болгон тодорхойлов. B25 үйлдлийн төлөвийг хадгалж, B26 тухайн session-ийн товч түүхийг буцаана. Локал хувилбарт memory list ашигласан. History дэлгэц болон durable store байхгүй тул FR-15-ыг бүхэлд нь хэрэгжсэн гэж тэмдэглээгүй.

API гэрээ ба хэрэгжүүлэлтийн ялгаа

Week 4-ийн архитектурын FastAPI/PostgreSQL сонголтыг өөрчлөөгүй. Энэ багцын Python standard-library сервер нь нэмэлт суулгалтгүй ажиллах contract sandbox юм. Production adapter, хэрэглэгчийн жинхэнэ session binding, scope validation, payload засах/цуцлах урсгал тусдаа хэрэгжинэ.

SPRINT 05  /  03

Authentication, schema ба алдаа




OpenAPI components/securitySchemes дотор **SandboxBearer** нь type: http, scheme: bearer. Global security бүх operation-д үйлчилнэ. Swagger Authorize талбарт **sprint05-local-sandbox** оруулна. Энэ нь нийтэд ил demo token; JWT биш, Google access token биш.

Production authentication-ийн хил

W4 ADR-002/003-ын дагуу B2 нь хэрэглэгчийн app session, provider OAuth scope, action owner болон version-ыг шалгана. Google refresh token browser/B3-д очихгүй. OAuth consent нь тухайн үйлдлийн агуулгыг баталсан гэсэн үг биш. Local sandbox зөвхөн bearer token болон session/version холбоосыг үзүүлнэ; OAuth permission байхгүй нөхцөлийг 403 failure hook-оор дуурайлгана.

| Reusable schema | Гол дүрэм |
| --- | --- |
| CommandRequest / Event | session_id, transcript, intent, event заавал. Calendar title, ISO date-time start/end, timezone шаардана. |
| VersionRequest | session_id + payload_version (integer ≥ 1); action ID нь path parameter. |
| CommandResponse / ActionResponse | status, user_message, correlation_id; action_id, version; execution-д resource ID. |
| Contact / HistoryEntry | Contact нэр/и-мэйл; history-д action ID, төрөл, төлөв, occurred_at. |
| Error | status, user_message, correlation_id, error.code, error.message. Token болон raw exception буцаахгүй. |

| HTTP | Нөхцөл ба засах алхам |
| --- | --- |
| 400 / 401 | Оролтын төрөл/талбар буруу; эсвэл bearer token дутуу. Body болон Authorize утгыг шалгана. |
| 403 / 404 / 409 | Permission unavailable; action олдохгүй; confirmation/version зөрсөн. Session, action, version-ыг шалгана. |
| 413 / 415 | 2 MiB-ээс их body; эсвэл media type буруу. PNG/WAV multipart, JSON content type сонгоно. |
| 500 / 503 | Дотоод эсвэл dependency алдаа. Correlation ID-аар оношилно; production Gmail unknown үр дүнг сохроор retry хийхгүй. |

X-Sandbox-Failure: 403, 500 эсвэл 503 header нь зөвхөн local error simulation. API contract-д ил тод тэмдэглэсэн; production control биш. Query parameter байхгүй; path ID зөвхөн confirm/execute-д хэрэглэнэ.

SPRINT 05  /  04

UE-5 · Зураг upload хийх жишээ




Corg.ly нь үндсэн AI төслөөс тусдаа сургалтын кейс. Chad-ийн эх код өгөөгүй тул доорх нь шаардсан endpoint-д зориулсан шинэ, ажилладаг орлуулах sample юм; хараагүй legacy кодын мөр бүрийг audit хийсэн гэж үзэхгүй.

Нэг удаагийн бэлтгэл

ZIP-ийг задалж Python 3.11+ ашиглана. Төслийн root-оос server.py-г эхлүүлээд өөр terminal дээр sample-уудыг ажиллуулна. Нэмэлт Python package шаардлагагүй; sample-ийн client.py helper болон assets-ийг хамт хадгална.

```
python server.py
# In another terminal:
python samples/upload_photo.py
```

POST /v1/pets/upload-photo

Einstein нэртэй pet fixture-ийн PNG файлыг multipart/form-data-аар илгээнэ. Photo field нь binary, pet_id нь текст. Included PNG нь жижиг синтетик fixture; бодит нохойн зураг биш.

```
"""Upload the included Einstein image fixture as multipart form data.
Run server.py first; this sample uses its documented sandbox token.
"""
from pathlib import Path
from client import multipart_file, post

photo_path = Path(__file__).resolve().parents[1] / "assets" / "einstein.png"
photo_body, photo_content_type = multipart_file(
    "photo", photo_path, "image/png", {"pet_id": "corgi_98231"})
post("/pets/upload-photo", body=photo_body, content_type=photo_content_type)

```

Серверээс авсан бодит local response · HTTP 200

```
{
  "pet_id": "corgi_98231",
  "photo_id": "photo_0001",
  "filename": "einstein.png",
  "bytes_received": 68
}
```

Хүлээн авсан byte тоог assets/einstein.png файлын хэмжээтэй тестээр тулгасан. Boundary болон media type-ийг client.py үүсгэж, HTTP алдаанд sample амжилтгүй дуусна. File замыг script-ийн байрлалаас шийдсэн тул terminal-ийн current directory-оос хамаарахгүй.

SPRINT 05  /  05

UE-5 · Аудио ба webhook




POST /v1/audio/translate-bark

Included WAV файлыг audio field-ээр илгээнэ. Аудио нь синтетик дуугүй fixture; meaning нь загварчилсан утга бөгөөд бодит bark inference хийдэггүй.

```
"""Submit the included synthetic WAV fixture to the bark-translation sandbox.
The returned meaning is a deterministic demonstration, not real audio inference.
"""
from pathlib import Path
from client import multipart_file, post

audio_path = Path(__file__).resolve().parents[1] / "assets" / "einstein-bark.wav"
audio_body, audio_content_type = multipart_file(
    "audio", audio_path, "audio/wav", {"pet_id": "corgi_98231"})
post("/audio/translate-bark", body=audio_body, content_type=audio_content_type)

```

Actual local response · HTTP 200

```
{
  "pet_id": "corgi_98231",
  "meaning": "I want to play.",
  "confidence": 0.92,
  "simulated": true
}
```

POST /v1/webhooks/subscribe

HTTPS callback URL болон pet activity event бүртгэнэ. example.org нь тайлбарын домэйн; sandbox callback илгээхгүй. Production-д эзэмшдэг хүлээн авагч URL хэрэгтэй.

```
"""Register an illustrative HTTPS callback for pet activity notifications.
The sandbox records the subscription but never sends outbound callbacks.
"""
from client import post

subscription = {
    "pet_id": "corgi_98231",
    "callback_url": "https://example.org/corgly/pet-activity",
    "events": ["pet.activity.detected"],
}
post("/webhooks/subscribe", subscription)

```

Actual local response · HTTP 201

```
{
  "subscription_id": "subscription_0001",
  "pet_id": "corgi_98231",
  "callback_url": "https://example.org/corgly/pet-activity",
  "events": [
    "pet.activity.detected"
  ],
  "status": "active"
}
```

SPRINT 05  /  06

Assistant sample ба туршилтын үр дүн




samples/assistant_workflow.py нь command, confirm, execute, contact search, history гэсэн таван HTTP хүсэлтийг дарааллаар ажиллуулна. Автомат demo-д урьдчилан хянасан fixture-ийг confirm хийдэг; бодит бүтээгдэхүүний UI хэрэглэгчийн ил тод сонголтыг заавал авна.

```
"""Propose, review-confirm and simulate one Calendar action, then read history.
This fixture is pre-reviewed for the automated demo; a real UI must ask the user.
"""
from client import post

command = {
    "session_id": "session_anu_01",
    "transcript": "Schedule the Sprint 05 review on 6 October at 10 AM.",
    "intent": "calendar.create",
    "event": {"title": "Sprint 05 review", "start": "2026-10-06T10:00:00+08:00",
              "end": "2026-10-06T10:30:00+08:00", "timezone": "Asia/Ulaanbaatar"},
}
proposal = post("/commands", command)
action_id = proposal["action_id"]
confirmation = {"session_id": "session_anu_01", "payload_version": proposal["payload_version"]}
post(f"/actions/{action_id}/confirm", confirmation)
post(f"/actions/{action_id}/execute", confirmation)
post("/contacts/search", {"query": "Anu"})
post("/sessions/history", {"session_id": "session_anu_01"})

```

Хамгаалалтын зан үйлийн бодит шалгалт

| Шалгалт | Ажигласан үр дүн |
| --- | --- |
| Баталгаажаагүй execute | 409; simulated provider write = 0. |
| Буруу version / өөр session | 409 / 404; action proposed хэвээр. |
| 30 execute retry | Нэг resource ID, нэг simulated write, нэг history entry. |
| 401 / 403 / 500 / 503 | Тодорхой Error envelope; failure simulation үед write = 0. |
| JSON, media, хэмжээ, цаг | Malformed/дутуу body = 400; буруу media = 415; их body = 413; end ≤ start = 400. |

Нийт 12 integration test амжилттай. Бүх 4 sample subprocess хэлбэрээр бодит local HTTP сервер рүү ажилласан. Үр дүн evidence/test-results.txt ба sample-responses.json-д бий. Энэ нь production NFR-03-ын 20 OAuth audit, бодит NFR-04 Calendar write, STT latency, keyboard accessibility тестийг орлохгүй.

SPRINT 05  /  07

Bhatti-ийн 5 зарчмын аудит




Үнэлгээ: 1-5 од буюу оноо. Хамрах хүрээ нь sample, shared helper, README, assets бүхий бүтэн багц. Энэ нь нотолгоонд тулгуурласан өөрийн аудит; хөндлөнгийн peer review биш.

| Sample | Expl. | Conc. | Clear | Usable | Trust. | Дундаж |
| --- | --- | --- | --- | --- | --- | --- |
| upload_photo.py | 5 | 4 | 5 | 5 | 4 | 4.6 |
| translate_bark.py | 5 | 4 | 5 | 5 | 4 | 4.6 |
| subscribe_webhook.py | 5 | 5 | 5 | 5 | 4 | 4.8 |
| assistant_workflow.py | 5 | 4 | 5 | 5 | 4 | 4.6 |
| client.py helper | 4 | 4 | 5 | 5 | 4 | 4.4 |

**Нийт: 115/125 = 92%, дундаж 4.60/5.00.** Зөвхөн заавал хийх Corg.ly гурван sample: 70/75 = 93.33%, дундаж 4.67/5.00. 80%-ийн босгыг давсан.

| Зарчим | Хэрэгжүүлэлт ба хязгаар |
| --- | --- |
| Explained · х.87 | Sample бүр purpose/prerequisite docstring-тэй. Helper-ийн setup README-д бий тул helper 4. |
| Concise · х.90 | HTTP болон multipart boilerplate-ийг client.py-д төвлөрүүлсэн. Multipart урт учир 4. |
| Clear · х.92 | photo_path, audio_body, auth token зэрэг утгатай нэр; explicit JSON, тогтмол indentation. |
| Usable · х.93 | Багцын assets, бодитоор ажиллах sandbox token; generic foo/bar payload байхгүй; timeout 10 сек. |
| Trustworthy · х.94 | Actual mock response ба HTTP status хадгалсан. Production provider шалгаагүй тул 4/5. |

CI bonus

.github/workflows/ci.yml нь YAML lint, бүх sample-ийн HTTP тест, docs build-ийг push/pull request дээр ажиллуулахаар бэлтгэгдсэн. Local run амжилттай; GitHub workflow ажилласан гэх нотолгоо байхгүй. Repository-д оруулсны дараа successful run URL-ийг тайланд нэмнэ.

Хуудасны ишлэлүүдийг Sprint 05 handout-ийн тайлбараар хэрэглэсэн. Номын бүрэн эх ирээгүй тул шинэ шууд эшлэл болон эхийг уншсан гэх баталгаа нэмээгүй.

SPRINT 05  /  08

Swagger UI ба Redoc




| Шалгуур | Swagger UI | Redoc CE |
| --- | --- | --- |
| Хайлт | Operation/tag filter. API туршилтын богино зам. | Search ба navigation-аар reference хайна. |
| Унших зохион байгуулалт | Operation нээхэд parameters, body, responses уртаар дэлгэнэ. | Desktop дээр navigation, тайлбар, example гэсэн 3 panel. |
| Try It Out | Token оруулж request илгээх, response status/body харах. | Энэ CE build нь унших reference; интерактив console ашиглаагүй. |
| Сонголт | Хөгжүүлэгчийн sandbox. | Нийтийн reference унших view. |

100-word decision report

For the Personal Voice AI Assistant, Redoc is the preferred public reference because its three panel layout keeps navigation, explanations, and examples visible together. Its search helps readers locate operations without expanding every section. Swagger UI is the better sandbox because developers can authorize requests, edit inputs, and inspect actual responses through Try It Out. Its operation filter supports quick lookup, although expanded requests make longer pages harder to scan. No timed search benchmark was conducted, so this comparison makes no speed claim. Publish both from the same validated specification: Redoc for reading, Swagger UI for supervised local sandbox experimentation.

Үгийн тоо: whitespace split аргаар яг 100. Search-ийн цаг хэмжсэн benchmark хийгээгүй; аль renderer хурдан гэсэн тоон дүгнэлт гаргаагүй.

Локал хаяг ба publication төлөв

```
http://127.0.0.1:8080/swagger/
http://127.0.0.1:8080/redoc.html
http://127.0.0.1:8080/corgly-redoc.html
```

Хоёр view browser-д харагдсан; screenshots evidence/ хавтсанд бий. API хүсэлтүүдийн гүйцэтгэлийг HTTP sample тестээр баталсан. Browser automation-аар Try It Out-ийн end-to-end товч даралтын гүйлт баталгаажаагүй. Redoc build нь version-тэй CDN script татдаг тул эхний load-д интернет хэрэгтэй.

Public URL хараахан үүсээгүй. DEPLOYMENT.md нь docs + Python sandbox-ийг ижил HTTPS origin дээр байрлуулах заавар, Dockerfile болон GitHub Pages workflow-тай. GitHub Pages дангаараа Python API ажиллуулахгүй тул functional public sandbox шалгуурыг бүрэн хангахгүй.

Харьцуулалтын эх: Redoc CE албан ёсны docs (3-panel layout), Swagger UI configuration (filter болон interactive settings). URL-ууд дараагийн хуудсанд бий.

SPRINT 05  /  09

Эргэцүүлэл ба Definition of Done




1. Bhatti Ch. 5-аас хэрэгжүүлсэн санаа

Trustworthy зарчим (handout-д х.94) нь зөв харагдах JSON бичихээс илүү бодитоор ажиллуулсан response хадгалахыг шаардсан. Энэ ажилд sample output-ийг ажилладаг mock серверээс авч OpenAPI example-д оруулсан. Mock evidence-ийг production evidence гэж нэрлэхгүй байх нь уг зарчмыг хэрэгжүүлсэн гол өөрчлөлт юм.

2. Chinchilla-аас цаашид хэрэглэх санаа

Handout-ийн Ch.2, х.18-22-т холбосон machine-readable API documentation чиглэлийг хэрэгжүүлэв. Нэг OpenAPI contract-оос хоёр renderer үүсгэх нь parameters, schema, error тайлбар зөрөх эрсдэлийг бууруулна. Номын эх ирээгүй тул энэ нь handout-ийн чиглүүлэгт тулгуурласан хэрэглээ бөгөөд тухайн хуудсыг бие даан нягталсан эшлэл биш.

3. Онол ба хэрэгжүүлэлтийн хамгийн том зөрүү

W4-т архитектурын mapping байсан ч provider-level нотолгоо дутуу байв. W5-д local contract болон sample тест нэмэгдсэн боловч жинхэнэ OAuth, confirmation UI, persistent state, Google retry semantics, STT latency батлагдаагүй. FR-15-ын API эзэн тодорхой болсон ч history UI ба бодит гурван төрлийн үйлдлийн T-FR15 туршилт үлдсэн.

| Definition of Done | Төлөв |
| --- | --- |
| ≥ 5 endpoint, OpenAPI 3.0.3, lint | Бэлэн: Assistant 5; Corg.ly 3; хоёр YAML validation амжилттай. |
| Spec repository-д commit хийх | Үлдсэн: repository холбоос өгөөгүй. |
| Public Swagger + Try It Out | Үлдсэн: local build/API tests бий; public service байхгүй. |
| Public Redoc + navigation/search | Үлдсэн: local rendered view бий; public URL байхгүй. |
| Audit ≥ 80%; decision report 100 үг | Бэлэн: 92%; 100 үг. |
| CI bonus | Workflow бэлэн, local tests pass; hosted run хийгдээгүй. |

Daily standup: 5 үндсэн endpoint lint-д тэнцсэн; 3 Corg.ly sample ба supporting код audit-д орсон; 4xx/5xx schema тодорхой. Retrospective: нэг contract болон actual payload нь consistency-г сайжруулсан; дараагийн алхам нь repository, hosting, production adapter evidence. Энэ нь болсон багийн хурлын протокол биш.

SPRINT 05  /  10

Эх сурвалж ба багцын индекс




Өмнөх ажлын суурь

1. software project documentation hw 1.pdf: х.1-2, Ану persona, authentication/scope/troubleshooting хэрэгцээ.<br/>2. software project documentation hw 2.pdf: үндсэн төслийн хамрах хүрээ; W3-ын шинэ baseline-ийг орлохгүй.<br/>3. software project documentation hw 3.pdf: х.1-3, SRS v1.0 FR-01-15 болон NFR шаардлагууд.<br/>4. software project documentation hw 4.pdf: х.5-9, B21-B25, FR-15 gap, ADR-002/003; х.13, W5 follow-up.

Даалгаврын болон албан ёсны эх

5. Sprint 05 Lab Instructions - OpenAPI 3.0 &amp; Bhatti Code Samples (1).pdf: US-5.1-5.4, UE-5, аудит, Definition of Done. Номын хуудасны дугаарууд энэ handout-оос дам ишилсэн.<br/>6. Redocly CLI lint: <link href="https://redocly.com/docs/cli/commands/lint" color="#007f82">redocly.com/docs/cli/commands/lint</link><br/>7. Redoc CE: <link href="https://redocly.com/docs/redoc" color="#007f82">redocly.com/docs/redoc</link><br/>8. Swagger UI configuration: <link href="https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/" color="#007f82">swagger.io - Swagger UI configuration</link>

Албан ёсны web эхүүдийг 2026-10-05-нд шалгасан. Энэ ажилд номын бүрэн эх болон Chad-ийн legacy code ирээгүй. Хувийн reflection-ийг өөрийн бодит суралцсан туршлагатай тулган хянаж ашиглана.

| Байршил | Агуулга |
| --- | --- |
| README.md / DEPLOYMENT.md | Ажиллуулах, validation, hosting ба үлдсэн acceptance checks. |
| docs/openapi/ | Assistant ба Corg.ly YAML; JSON mirror. YAML нь docs build-ийн эх. |
| samples/ / assets/ | 3 mandatory Corg.ly sample, assistant workflow, shared client; PNG/WAV fixtures. |
| server.py / tests/ | Local sandbox ба 12 integration test. |
| public/ | Swagger UI, Assistant Redoc, Corg.ly Redoc. |
| evidence/ | Actual responses, lint/test logs, renderer screenshots. |
| .github/workflows/ | CI validation болон manual Pages publication. |
| docs/audit-scorecard.md | Sample бүрийн оноо, тайлбар, evidence scope. |
| docs/decision-report.md | Яг 100 үгтэй англи comparative report. |