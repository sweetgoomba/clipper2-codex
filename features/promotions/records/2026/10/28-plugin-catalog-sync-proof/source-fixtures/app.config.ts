import { ApplicationConfig, ErrorHandler, inject, provideAppInitializer, provideZonelessChangeDetection } from '@angular/core';
import { RouteReuseStrategy, provideRouter, withHashLocation } from '@angular/router';
import { provideHttpClient, withInterceptors, withXhr } from '@angular/common/http';
import { httpLoggingInterceptor } from '@core/logging/http-logging.interceptor';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { MAT_SNACK_BAR_DEFAULT_OPTIONS } from '@angular/material/snack-bar';
import { OVERLAY_DEFAULT_CONFIG } from '@angular/cdk/overlay';
import { ToolReadinessClient, HttpToolReadinessClient } from '@core/readiness/tool-readiness.client';
import { HttpMediaLibraryApi, MediaLibraryApi } from '../core/media-library/media-library.api';
import { HttpTtsApi, TtsApi } from '../core/tts/tts-api';
import { StorageApi, HttpStorageApi } from '../core/storage/storage.api';
import { VariationV2Api } from '../features/variation-v2/services/variation-v2-api';
import { HttpVariationV2Api } from '../features/variation-v2/services/http-variation-v2-api';

import { routes } from './app.routes';
import {
  providePipelineFeature,
  provideBackendLocator,
  PluginStatusService,
  pluginFeatureNavigation,
  type PluginFeatureName,
} from '@core';
import { ThemeService } from '@core/theme/theme.service';
import { RendererErrorHandler } from '@core/logging/renderer-error-handler';
import { GlobalErrorCapture } from '@core/logging/global-error-capture';
import { SystemNoticeService } from '@core/electron/system-notice.service';
import { provideDanceApi } from '@features/dance-highlight/dance-highlight.providers';
import { AuthStore } from '../core/auth/auth.store';
import { KeepAliveRouteReuseStrategy } from '../core/navigation/keep-alive-route-reuse.strategy';
import { OperationRecoveryService } from '../core/operations/operation-recovery.service';
import { DefaultMediaSession } from '../core/media-library/default-media-session.service';
import { provideAuthBackend } from '../core/auth/auth-backend';
import { localApiAuthInterceptor } from '../core/auth/local-api-auth.interceptor';
import { devErrorSimulationInterceptor } from '../core/errors/dev-error-simulation.interceptor';
import { provideShortformDirectorProfileGateway } from '../features/shortform-director/services/shortform-director-profile.service';
import { provideShortformDirectorResearchGateway } from '../features/shortform-director/services/shortform-director-research.service';
import { provideShortformDirectorCandidateGateway } from '../features/shortform-director/services/shortform-director-candidate.service';
import { provideShortformDirectorProductionGateway } from '../features/shortform-director/services/shortform-director-production.service';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZonelessChangeDetection(),
    provideRouter(routes, withHashLocation()),
    // data.keepAlive 라우트(숏폼 만들기 3화면)는 떠날 때 숨겨 두었다가 다시 붙인다(2026-10-13 ISS-047).
    { provide: RouteReuseStrategy, useExisting: KeepAliveRouteReuseStrategy },
    // devErrorSimulation은 체인 맨 뒤 — 로깅 인터셉터가 시뮬레이션 실패도 로그 뷰어에 남긴다.
    provideHttpClient(withXhr(), withInterceptors([
      localApiAuthInterceptor,
      httpLoggingInterceptor,
      devErrorSimulationInterceptor,
    ])),
    provideAnimationsAsync(),
    // 스낵바 전역 위치 정책: 우상단 고정 + 기본 4000ms. duration을 생략하는 앞으로의 호출도
    // 이 기본값을 물려받아 "영원히 안 사라짐" 사고를 막는다. 에러 경로(ErrorNotificationService)는
    // 이 기본값을 무력화하려면 duration: undefined를 명시해야 한다 — 생략은 무한이 아니라 4초다.
    { provide: MAT_SNACK_BAR_DEFAULT_OPTIONS, useValue: { horizontalPosition: 'end', verticalPosition: 'top', duration: 4000 } },
    // 오버레이(select 펼침 목록·메뉴·툴팁·대화상자)는 Angular 19 때처럼 body 끝 컨테이너에 그린다.
    // 22부터 기본이 네이티브 popover라 **트리거 바로 옆 DOM**에 붙는데, 그러면 트리거를 감싼 부모의
    // 하위선택자가 판 안까지 번진다(mat-list-item 안 mat-select의 줄 글자가 10px 밀렸다 — 저장공간 >
    // 자동 정리). 앱 전역 스타일(styles.scss의 `.cdk-overlay-pane …`)도 전부 컨테이너 전제로 쓰였다.
    // 대가: 컨테이너는 z-index 1000이라 top layer가 아니다. 생성 중 모달(`app-generating-overlay`)은 작업 영역 안
    // z-index 99라 셸 층(메뉴 100·소식 패널 101·설치 토스트 300)보다 아래이고, 토스트·대화상자는 컨테이너가
    // app-root 밖(body)이라 그 위에 뜬다. 그 밖엔 top layer에 기대는 곳이 없다
    // (네이티브 popover·<dialog> 0곳).
    { provide: OVERLAY_DEFAULT_CONFIG, useValue: { usePopover: false } },
    { provide: ErrorHandler, useClass: RendererErrorHandler },
    provideAuthBackend(),
    providePipelineFeature({ ...pipelineFeatureNavigation('proof_new_plugin'), loadComponent: () => import('../features/person-highlight/pages/person-setup/person-setup.component').then(m => m.PersonSetupComponent) }),
    provideAppInitializer(() => { inject(ThemeService); }),
    provideAppInitializer(() => {
      inject(GlobalErrorCapture).install();
    }),
    // N1/N2(2026-08-24): main 크래시·nest 종료 통보 구독. 브라우저 dev(clipperBridge 없음)에서는
    // install()이 조용히 no-op.
    provideAppInitializer(() => {
      inject(SystemNoticeService).install();
    }),
    // 앱 시작 시 세션 복원 — 비동기 fire-and-forget(부팅 막지 않음).
    provideAppInitializer(() => {
      inject(OperationRecoveryService);
      // 기본 제공 목록 갱신·받기 진행(spec 2026-10-14 D5) — 로그인 사용자가 정해질 때 스스로 돈다.
      inject(DefaultMediaSession);
      void inject(AuthStore).loadSession();
    }),
    provideBackendLocator(),
    provideShortformDirectorProfileGateway(),
    provideShortformDirectorResearchGateway(),
    provideShortformDirectorCandidateGateway(),
    provideShortformDirectorProductionGateway(),
    { provide: ToolReadinessClient, useClass: HttpToolReadinessClient },
    { provide: MediaLibraryApi, useClass: HttpMediaLibraryApi },
    { provide: TtsApi, useClass: HttpTtsApi },
    { provide: StorageApi, useClass: HttpStorageApi },
    // 홈 실행 큐가 베리에이션 배치를 한 줄로 접고 그 줄의 [취소]로 배치를 통째로 취소한다
    // (V15 D4). 큐는 `variation` 라우트 밖(홈)이라 그 라우트 스코프 provider
    // (`provideVariationV2()`)에 닿지 못한다 — 루트에도 실제 구현을 꽂아 둔다.
    { provide: VariationV2Api, useClass: HttpVariationV2Api },
    provideDanceApi(),
    providePipelineFeature({
      ...pipelineFeatureNavigation('dance_highlight'),
      loadComponent: () =>
        import('../features/dance-highlight/pages/dance-setup/dance-setup.component').then(
          (m) => m.DanceSetupComponent,
        ),
    }),
    providePipelineFeature({
      ...pipelineFeatureNavigation('dialog_highlight'),
      loadComponent: () =>
        import('../features/dialog-highlight/pages/dialog-setup/dialog-setup.component').then(
          (m) => m.DialogSetupComponent,
        ),
    }),
    providePipelineFeature({
      ...pipelineFeatureNavigation('person_highlight'),
      loadComponent: () =>
        import('../features/person-highlight/pages/person-setup/person-setup.component').then(
          (m) => m.PersonSetupComponent,
        ),
    }),
    providePipelineFeature({
      ...pipelineFeatureNavigation('comment_overlay'),
      loadComponent: () =>
        import('../features/comment-overlay/pages/comment-overlay-setup/comment-overlay-setup.component').then(
          (m) => m.CommentOverlaySetupComponent,
        ),
    }),
    providePipelineFeature({
      ...pipelineFeatureNavigation('shortform_url'),
      loadComponent: () =>
        import('../features/shortform/pages/shortform-workflow-page/shortform-workflow-page.component').then(
          (m) => m.ShortformWorkflowPageComponent,
        ),
    }),
    providePipelineFeature({
      ...pipelineFeatureNavigation('shortform_paste'),
      loadComponent: () =>
        import('../features/shortform/pages/shortform-workflow-page/shortform-workflow-page.component').then(
          (m) => m.ShortformWorkflowPageComponent,
        ),
    }),
    providePipelineFeature({
      ...pipelineFeatureNavigation('shortform_prompt'),
      loadComponent: () =>
        import('../features/shortform/pages/shortform-workflow-page/shortform-workflow-page.component').then(
          (m) => m.ShortformWorkflowPageComponent,
        ),
    }),
    providePipelineFeature({
      ...pipelineFeatureNavigation('shortform_article'),
      loadComponent: () =>
        import('../features/shortform/pages/shortform-workflow-page/shortform-workflow-page.component').then(
          (m) => m.ShortformWorkflowPageComponent,
        ),
    }),
    providePipelineFeature({
      ...pipelineFeatureNavigation('shortform_explainer'),
      loadComponent: () =>
        import('../features/shortform/pages/shortform-workflow-page/shortform-workflow-page.component').then(
          (m) => m.ShortformWorkflowPageComponent,
        ),
    }),
    providePipelineFeature({
      ...pipelineFeatureNavigation('shortform_director'),
      loadComponent: () =>
        import('../features/shortform-director/layout/shortform-director-shell/shortform-director-shell.component').then(
          (m) => m.ShortformDirectorShellComponent,
        ),
    }),
    providePipelineFeature({
      ...pipelineFeatureNavigation('variation'),
      loadComponent: () =>
        import('../features/variation-v2/pages/v2-project-list/v2-project-list.component').then(
          (m) => m.V2ProjectListComponent,
        ),
    }),
    providePipelineFeature({
      ...pipelineFeatureNavigation('ranking'),
      loadComponent: () =>
        import('../features/ranking/pages/ranking-setup/ranking-setup.component').then(
          (m) => m.RankingSetupComponent,
        ),
    }),
    providePipelineFeature({
      ...pipelineFeatureNavigation('curation'),
      loadComponent: () =>
        import('../features/curation/pages/curation-page/curation-page.component').then(
          (m) => m.CurationPageComponent,
        ),
    }),
    providePipelineFeature({
      ...pipelineFeatureNavigation('overseas_dub'),
      loadComponent: () =>
        import('../features/overseas-dub/pages/overseas-dub-page/overseas-dub-page.component').then(
          (m) => m.OverseasDubPageComponent,
        ),
    }),
    provideAppInitializer(() => {
      void inject(PluginStatusService).refreshAll();
    }),
  ],
};

function pipelineFeatureNavigation(name: PluginFeatureName) {
  const metadata = pluginFeatureNavigation(name);
  return {
    name,
    displayName: metadata.navLabel,
    icon: metadata.icon,
    route: metadata.route,
  };
}
