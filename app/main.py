import secrets
from datetime import date

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.clients.nissan import NISSAN_TEMPLATE_PATH
from app.config import settings
from app.jira.client import JiraClient
from app.jira.models import ScopeParams
from app.jira.service import JiraDataService
from app.reports.excel.builder import ExcelReportBuilder
from app.reports.pptx.builder import PptxReportBuilder

app = FastAPI(title="Nissan Report Tool")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
security = HTTPBasic()


def require_auth(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    """Single shared username/password gate — this MVP has no per-user auth,
    so this is the minimum bar before the tool is exposed to the team."""
    user_ok = secrets.compare_digest(credentials.username, settings.app_basic_auth_user)
    pass_ok = secrets.compare_digest(credentials.password, settings.app_basic_auth_password)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


def get_jira_service() -> JiraDataService:
    client = JiraClient(settings.jira_base_url, settings.jira_email, settings.jira_api_token)
    return JiraDataService(client)


@app.get("/")
def index(request: Request, _: None = Depends(require_auth)):
    return templates.TemplateResponse(request, "index.html")


@app.post("/export/excel")
def export_excel(
    start_date: date = Form(...),
    end_date: date = Form(...),
    _: None = Depends(require_auth),
):
    scope = ScopeParams(start_date=start_date, end_date=end_date, project_key=settings.jira_project_key)
    bundle = get_jira_service().fetch_full_scope_bundle(scope)
    buf = ExcelReportBuilder().build(bundle)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="JiraExport_{start_date}_{end_date}.xlsx"'},
    )


@app.post("/export/pptx")
def export_pptx(
    start_date: date = Form(...),
    end_date: date = Form(...),
    _: None = Depends(require_auth),
):
    scope = ScopeParams(start_date=start_date, end_date=end_date, project_key=settings.jira_project_key)
    bundle = get_jira_service().fetch_full_scope_bundle(scope)
    buf = PptxReportBuilder(NISSAN_TEMPLATE_PATH).build(bundle)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="MonthlyReport_{start_date}_{end_date}.pptx"'},
    )
