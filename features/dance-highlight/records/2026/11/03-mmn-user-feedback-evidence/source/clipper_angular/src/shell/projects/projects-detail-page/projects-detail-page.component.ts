import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  effect,
  inject,
  signal,
  untracked,
} from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import {
  AssignDanceMemberRequest,
  ClipTrim,
  JobHistoryService,
  ProjectClipItem,
  ProjectDetail,
  ProjectHistoryService,
  ProjectPersonItem,
  PersonEditAction,
  pluginFeatureMetadata,
} from '@core';
import { NavHistoryService } from '@core/navigation/nav-history.service';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Clipboard } from '@angular/cdk/clipboard';
import { ConfirmDialogService } from '../../../shared/ui/confirm-dialog/confirm-dialog.service';
import { formatArtistDisplayName } from '../../../shared/format/artist-display-name';
import { appErrorFrom } from '../../../core/errors/app-error';
import { ErrorNotificationService } from '../../../core/errors/error-notification.service';
import { RendererLogger } from '../../../core/logging/renderer-logger';
import { FileDownloadService, FileSaveResult } from '../../../core/download/file-download.service';
import { fileTimestamp, safeFilePart } from '../../../core/download/download-filename';
import { DanceResultDetailComponent } from '../dance-result-detail/dance-result-detail.component';
import { DanceDiagnosticTimelineComponent } from '../dance-diagnostic-timeline/dance-diagnostic-timeline.component';
import { DialogResultDetailComponent } from '../dialog-result-detail/dialog-result-detail.component';
import { PersonResultDetailComponent } from '../person-result-detail/person-result-detail.component';
import { ProjectsClipOverlayComponent } from '../projects-clip-overlay/projects-clip-overlay.component';
import { AppStatePanelComponent } from '../../../shared/ui/app-state-panel/app-state-panel.component';
import { PageLoadingComponent } from '../../../shared/ui/page-loading';
import { PageComponent } from '../../../shared/layout/page/page.component';
import { PageActionsDirective } from '../../../shared/layout/page/page-actions.directive';
import {
  highlightShortformRequestFromManifest,
  type SavedHighlightShortform,
  type HighlightShortformRestore,
} from '@features/highlight-shortform/models/highlight-shortform';
import {
  pluginLabel as formatPluginLabel,
  personLabel,
} from '../utils/projects-formatters';
import { asyncAction } from '@shared/async/async-action';
import { sortPersonCandidates } from '../utils/person-candidates';

/** 원본 비율 클립 준비 대기 중 상세를 다시 받는 간격(T13 D5). */
const RAW_CLIP_POLL_MS = 3000;
/** 이만큼 계속 준비 중이면 간격을 늘린다 — 백필이 막혔을 수 있다(서버는 3번 실패하면 포기한다). */
const RAW_CLIP_POLL_BACKOFF_AFTER_MS = 2 * 60 * 1000;
const RAW_CLIP_POLL_SLOW_MS = 15000;
/** 이만큼 계속 준비 중이면 폴링을 멈추고 다시 열어 달라고 알린다(끝없이 묻지 않게). */
const RAW_CLIP_POLL_GIVE_UP_MS = 10 * 60 * 1000;
const RAW_CLIP_POLL_GAVE_UP_MESSAGE = '원본 비율 클립 준비가 오래 걸리고 있어요. 잠시 후 다시 열어 주세요';
/** 폴링이 연달아 이만큼 실패하면 멈추고 알린다. */
const RAW_CLIP_POLL_MAX_FAILURES = 5;
/** 숏폼 카드 [편집] 복원 — 생성 때 고른 클립 일부가 지금은 없을 때(T13). */
const SHORTFORM_RESTORE_PARTIAL_MESSAGE = '일부 클립이 없어져 나머지만 불러왔어요';
/** 숏폼 카드 [편집] 복원 — 고른 클립이 하나도 안 남아 설정만 되살렸을 때. */
const SHORTFORM_RESTORE_SETTINGS_ONLY_MESSAGE = '저장된 클립을 찾지 못해 설정만 불러왔어요';

@Component({
  selector: 'app-projects-detail-page',
  imports: [
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    DanceResultDetailComponent,
    DanceDiagnosticTimelineComponent,
    DialogResultDetailComponent,
    PersonResultDetailComponent,
    ProjectsClipOverlayComponent,
    AppStatePanelComponent,
    PageLoadingComponent,
    PageComponent,
    PageActionsDirective,
  ],
  templateUrl: './projects-detail-page.component.html',
  styleUrl: './projects-detail-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProjectsDetailPageComponent implements OnInit {
  readonly projects = inject(ProjectHistoryService);

  readonly detail = signal<ProjectDetail | null>(null);
  readonly danceStep = signal<'map' | 'result'>('result');
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly selectedClipId = signal<string | null>(null);
  /** ① 인물 칸에서 고른 인물(personId). 안무 전용. */
  readonly selectedPersonId = signal<string | null>(null);
  readonly clipOverlayId = signal<string | null>(null);
  readonly clipOverlayIds = signal<string[]>([]);
  /**
   * 숏폼 카드 [편집](`?fromShortform={jobId}`)으로 들어왔을 때 결과 화면에 한 번 넘길 값(T13).
   * 숏폼 입력 상태(Draft)는 결과 화면 컴포넌트가 가지므로, 여기선 지금 상세에 남은 클립만
   * 추려 넘기고 적용은 자식이 한다.
   */
  readonly shortformRestore = signal<HighlightShortformRestore | null>(null);

  /** ① 인물 칸 행 — 안무만. `detail.persons` 기준(안무 `renders`는 늘 비어 있다, T12). */
  readonly visiblePersons = computed(() => {
    const detail = this.detail();
    if (!detail) return [];
    if (detail.category === 'person') return visiblePersonCandidates(detail);
    return detail.category === 'dance' ? visibleDancePersons(detail.persons) : [];
  });
  readonly selectedClip = computed(() => {
    const detail = this.detail();
    const clipId = this.selectedClipId();
    if (!detail || !clipId) return null;
    return detail.clips.find((clip) => clip.clipId === clipId) ?? null;
  });
  /** 고른 인물이 (삭제·이동으로) 인물 칸에서 사라졌으면 null — 빈 선택으로 돌아간다. */
  readonly selectedPerson = computed(() => {
    const personId = this.selectedPersonId();
    if (!personId) return null;
    return this.visiblePersons().find((person) => person.personId === personId) ?? null;
  });
  /** 인물 미선택이면 빈 목록 — 전체 클립을 넘기면 ② 체크·생성 대상이 전 클립으로 보인다.
   *  선택되면 그 인물의 clipIds만 — 백엔드가 clipIds를 최종 클립으로 다시 계산해 주므로(D7)
   *  personId 폴백이 필요 없다. */
  readonly selectedPersonClips = computed(() => {
    const detail = this.detail();
    if (!detail) return [];
    const person = this.selectedPerson();
    if (!person) return [];
    const clipIds = new Set(person.clipIds);
    return detail.clips.filter((clip) => clipIds.has(clip.clipId));
  });
  readonly overlayClip = computed(() => {
    const detail = this.detail();
    const clipId = this.clipOverlayId();
    if (!detail || !clipId) return null;
    return detail.clips.find((clip) => clip.clipId === clipId) ?? null;
  });
  readonly canNavigateOverlay = computed(() => this.clipOverlayIds().length > 1);
  /**
   * 오버레이 헤더의 `13 / 24`. `clipOverlayIds`/`clipOverlayId`는 이미 이 컴포넌트가 들고 있으므로
   * 여기서 한 번만 구해 오버레이엔 input으로 넘긴다 — 자식이 같은 계산을 다시 하지 않는다.
   */
  readonly overlayClipIndex = computed(() => {
    const ids = this.clipOverlayIds();
    const currentId = this.clipOverlayId();
    if (!currentId) return null;
    const index = ids.indexOf(currentId);
    return index >= 0 ? index + 1 : null;
  });
  readonly overlayClipCount = computed(() => this.clipOverlayIds().length);

  /**
   * 헤더 제목 = **모듈 이름**(좌측 nav와 같은 문자열). 다른 모듈 화면처럼 "지금 어느 모듈에
   * 있나"를 말한다 — 영상 제목은 부제로 내려간다(spec 2026-09-19-result-page-header-unify).
   * 상세를 아직(또는 끝내) 못 불러온 화면에도 헤더는 그려지므로 폴백이 필요하다 —
   * 제목 없이 두면 `<app-page>`의 필수 title 계약이 빈 문자열로 채워져 헤더가 반쪽이 된다.
   */
  readonly pageTitle = computed(() => {
    const project = this.detail();
    return project ? formatPluginLabel(project.pluginName) : '프로젝트 결과';
  });

  /** 헤더 부제 = 보고 있는 대상(영상 제목). 길면 공유 헤더가 말줄임 + 호버 툴팁으로 처리한다. */
  readonly pageSubtitle = computed(() => this.detail()?.title ?? '');

  readonly sourceUrl = computed(() => {
    const detail = this.detail();
    if (detail?.category !== 'dance' && detail?.category !== 'dialog' && detail?.category !== 'person') return null;
    const source = detail.sourceAssets?.find((asset) => asset.type === 'video');
    if (!source || source.originalInput.type !== 'youtube_url') return null;
    return source.provenance.originalUrl || source.originalInput.url || null;
  });
  readonly sourceUrlAction = computed(() => this.sourceUrl() ? { icon: 'link', label: '원본 URL 복사' } : null);

  readonly artistBadge = computed(() => {
    const detail = this.detail();
    if (detail?.category !== 'dance') return '';
    const setup = detail.params['dance_setup'];
    if (!setup || typeof setup !== 'object' || Array.isArray(setup)) return '';
    const { artistDisplayName, artistName } = setup as Record<string, unknown>;
    return formatArtistDisplayName(
      typeof artistName === 'string' ? artistName : '',
      typeof artistDisplayName === 'string' ? artistDisplayName : undefined,
    );
  });

  /**
   * 헤더 좌측 아이콘 = 좌측 nav가 그 플러그인에 쓰는 바로 그 아이콘(안무=taunt,
   * 대사=format_quote). 옛 제목 블록의 eyebrow(플러그인 이름)가 하던 "이게 무슨 결과물인지"를
   * 아이콘이 이어받는다. 모르는 플러그인이면 null — 아이콘 없이 렌더된다.
   */
  readonly pageIcon = computed(
    () => pluginFeatureMetadata(this.detail()?.pluginName ?? '')?.icon ?? null,
  );

  /** 저장 중인 클립 id. 그 클립의 트리머만 잠기고, 중복 저장도 이걸로 막는다. */
  readonly trimmingClipId = signal<string | null>(null);
  /**
   * 저장 직후 플레이어가 리로드된다 — 그때 되돌려 놓을 위치.
   * `seq`가 있어야 **같은 초로 두 번 저장**할 때도(끝 손잡이만 옮긴 경우) 값이 달라져 다시 적용된다.
   */
  readonly restoreSeek = signal<{ sec: number; seq: number } | null>(null);
  private restoreSeq = 0;

  readonly zipping = signal(false);

  /** 클립 수 = ZIP 버튼 라벨의 (N). 0이면 버튼 비활성. */
  readonly zipCount = computed(() => {
    const detail = this.detail();
    return detail?.clips?.filter((clip) => canExportClip(detail, clip)).length ?? 0;
  });
  /**
   * 결과 편집 요청 ~ 상세 재조회(`load()`) 끝까지 true. 이동 동안 편집 버튼·체크·드래그를 전부 잠근다
   * (스낵바 「실행취소」처럼 누른 부품이 사라지는 경우도 이 잠금이 곧 표시다).
   *
   * `asyncAction` 대신 진행·대기 중인 편집 수로 센다 — 실행취소는 누른 스낵바가 이미 사라져서
   * 다른 편집이 도는 중이라고 **버리면 안 된다**(조용히 사라졌다). 실행취소는 편집 줄
   * (`editChain`) 뒤에 서서 앞 편집이 끝나면 이어서 돌고, 그동안 잠금도 계속 켜져 있다.
   */
  private readonly editsInFlight = signal(0);
  readonly editing = computed(() => this.editsInFlight() > 0);
  /** 편집 줄 — 앞 편집이 끝나야(성공·실패 무관) 다음이 시작된다. 절대 reject되지 않게 유지한다. */
  private editChain: Promise<unknown> = Promise.resolve();
  /** `?fromShortform=` 복원 중 — 체크·설정 칸을 잠가 먼저 고친 값을 덮어쓰지 않게 한다. */
  private readonly restoreAction = asyncAction();
  readonly restoring = this.restoreAction.pending;

  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly navHistory = inject(NavHistoryService);
  private readonly confirmDialog = inject(ConfirmDialogService);
  private readonly jobs = inject(JobHistoryService);
  private readonly notify = inject(ErrorNotificationService);
  private readonly clipboard = inject(Clipboard);
  private readonly fileDownload = inject(FileDownloadService);
  private readonly snackBar = inject(MatSnackBar);

  copySourceUrl(): void {
    const url = this.sourceUrl();
    if (!url) return;
    if (this.clipboard.copy(url)) this.notify.showSuccess('원본 URL을 복사했습니다.');
    else this.notify.showTransientMessage('원본 URL을 복사하지 못했습니다.');
  }

  /** 대사 클립 중 원본 비율 클립을 아직 만드는 중인 게 있다(백필, T13 D5). */
  private readonly hasPendingRawClip = computed(() => {
    const detail = this.detail();
    return detail?.category === 'dialog' && detail.clips.some((clip) => clip.rawStatus === 'pending');
  });
  private rawClipPollInFlight = false;
  private rawClipPollFailures = 0;
  /** 준비 중 클립이 **계속** 있기 시작한 시각. 다 준비되면 지운다(다음 대기는 새로 잰다). */
  private rawClipPendingSinceMs: number | null = null;
  /** 연속 실패로 폴링을 멈췄다 — 다시 켜지 않는다(화면을 다시 열면 새 인스턴스라 초기화된다). */
  private readonly rawClipPollStopped = signal(false);
  private readonly logger = inject(RendererLogger);

  constructor() {
    // 준비 중인 클립이 있는 동안만 조용히 다시 불러와 완료를 알아챈다. 다 준비되거나(신호가
    // false로) 화면을 떠나면(effect 파괴) 정리 함수가 타이머를 끊는다.
    // 2분이 넘으면 15초 간격으로 늦추고, 10분이 넘으면 멈추고 알린다.
    effect((onCleanup) => {
      if (!this.hasPendingRawClip()) {
        this.rawClipPendingSinceMs = null;
        return;
      }
      if (this.rawClipPollStopped()) return;
      const projectId = untracked(() => this.detail()?.projectId);
      if (!projectId) return;
      const since = this.rawClipPendingSinceMs ??= Date.now();
      let timer: ReturnType<typeof setTimeout> | undefined;
      const schedule = (): void => {
        const elapsed = Date.now() - since;
        const delay = elapsed >= RAW_CLIP_POLL_BACKOFF_AFTER_MS ? RAW_CLIP_POLL_SLOW_MS : RAW_CLIP_POLL_MS;
        timer = setTimeout(() => {
          if (Date.now() - since >= RAW_CLIP_POLL_GIVE_UP_MS) {
            this.rawClipPollStopped.set(true);
            this.snackBar.open(RAW_CLIP_POLL_GAVE_UP_MESSAGE, '닫기', { duration: 6000 });
            return;
          }
          // 다음 틱을 먼저 건다 — 앞 요청이 늦으면 `pollRawClips`가 알아서 건너뛴다.
          schedule();
          void this.pollRawClips(projectId);
        }, delay);
      };
      schedule();
      onCleanup(() => clearTimeout(timer));
    });
  }

  async ngOnInit(): Promise<void> {
    const projectId = this.route.snapshot.paramMap.get('projectId');
    if (!projectId) {
      this.error.set('프로젝트를 찾지 못했습니다.');
      return;
    }
    await this.load(projectId);
    const shortformJobId = this.route.snapshot.queryParamMap.get('fromShortform');
    if (shortformJobId) {
      this.danceStep.set('result');
      await this.restoreFromShortform(shortformJobId);
    }
  }

  /**
   * 헤더 「뒤로」 — 들어온 화면(홈)으로, 딥링크·새로고침이면 홈으로. 홈 카드로 들어간 다른 화면들과 같은 이름·같은 길이다.
   * 고정 `/projects`로 보내면 홈 주소의 유형·정렬 필터(`?type=`·`?sort=`)가 날아간다. 이 화면 안의 주소 바꾸기는 전부
   * `replaceUrl`이라 직전 기록이 이 화면 자신일 일은 없다.
   */
  goBack(): void {
    this.navHistory.back(['/projects']);
  }

  selectClip(clip: ProjectClipItem): void {
    this.selectedClipId.set(clip.clipId);
  }

  selectPerson(person: ProjectPersonItem): void {
    this.selectedPersonId.set(person.personId);
    if (this.detail()?.category === 'person') {
      const ids = new Set(person.clipIds);
      this.selectedClipId.set(this.detail()?.clips.find((clip) => ids.has(clip.clipId) && !clip.excluded)?.clipId
        ?? this.detail()?.clips.find((clip) => ids.has(clip.clipId))?.clipId ?? null);
    }
  }

  /** 인물 편집 한 건의 결과 — 모든 호출이 성공/실패(무시된 호출 포함)로 끝나 자식(이름 입력칸)이 잠금을 풀 수 있게 한다. */
  readonly personEditOutcome = signal<{ ok: boolean } | null>(null);

  async onPersonEdit(action: PersonEditAction): Promise<void> {
    const ok = await this.performPersonEdit(action);
    this.personEditOutcome.set({ ok });
  }

  private async performPersonEdit(action: PersonEditAction): Promise<boolean> {
    const project = this.detail();
    if (!project || project.category !== 'person') return false;
    const successMessage = this.personEditSuccessMessage(project, action);
    const done = await this.runEdit(async () => {
      try {
        await this.projects.editPerson(project.projectId, action);
        if ((action.type === 'merge' || action.type === 'move_clips')
          && this.selectedPersonId() === action.sourcePersonId) {
          this.selectedPersonId.set(action.targetPersonId);
        }
        await this.load(project.projectId, { keepSelectedClip: true });
        if (this.detail()) this.snackBar.open(successMessage, '닫기', { duration: 4000 });
        return true;
      } catch (error) {
        this.notify.showToast(appErrorFrom(error));
        return false;
      }
    });
    return done === true;
  }

  private personEditSuccessMessage(project: ProjectDetail, action: PersonEditAction): string {
    const name = (personId: string) => personLabel(
      project.persons.find((person) => person.personId === personId) ?? { personId, clipIds: [] },
    );
    switch (action.type) {
      case 'merge': return `${name(action.sourcePersonId)} → ${name(action.targetPersonId)} 병합 완료`;
      case 'move_clips': return `장면 ${action.clipIds.length}개 → ${name(action.targetPersonId)} 이동 완료`;
      case 'remove_clips': return `${name(action.personId)}에서 장면 ${action.clipIds.length}개를 제거했습니다`;
      case 'delete_person': return `${name(action.personId)} 삭제 완료`;
      default: return '변경 사항을 저장했습니다';
    }
  }

  openClipOverlay(event: { clip: ProjectClipItem; clips: ProjectClipItem[] }): void {
    const clipIds = event.clips.map((clip) => clip.clipId);
    this.clipOverlayIds.set(clipIds.length > 0 ? clipIds : [event.clip.clipId]);
    this.clipOverlayId.set(event.clip.clipId);
  }

  /** 사용자가 누른 편집 — 이미 편집 중(실행취소 대기 포함)이면 무시한다(연타 가드, `asyncAction`과 같은 계약). */
  private runEdit<T>(fn: () => Promise<T>): Promise<T | undefined> {
    if (this.editing()) return Promise.resolve(undefined);
    return this.enqueueEdit(fn);
  }

  /**
   * 실행취소 — 버리지 않는다. 앞 편집이 끝날 때까지 기다렸다 반드시 돌고, 앞 편집이 실패해도 막히지 않는다.
   * 잠금(`editing`)은 줄에 선 순간 켜진다(첫 await 전). 줄이 비어 있으면 기다리지 않고 바로 보낸다.
   */
  private enqueueEdit<T>(fn: () => Promise<T>): Promise<T> {
    const idle = this.editsInFlight() === 0;
    this.editsInFlight.update((n) => n + 1);
    // executor는 동기로 돈다 — 줄이 비면 요청이 같은 틱에 나가고, 동기 throw도 reject로 바뀌어 잠금이 안 남는다.
    const start = () => new Promise<T>((resolve) => resolve(fn()));
    const result = idle ? start() : this.editChain.then(start);
    this.editChain = result.catch(() => undefined);
    return result.finally(() => this.editsInFlight.update((n) => n - 1));
  }

  /**
   * 배정은 지도에 줄 하나 적는 것이라 되돌릴 수 있다 — 확인 모달 대신 스낵바의
   * 「실행취소」가 그 역할을 더 가볍게 한다(사용자 승인, 확인 모달 걷어냄).
   */
  async assignDancePerson(request: AssignDanceMemberRequest): Promise<void> {
    const detail = this.detail();
    if (!detail || this.zipping()) return;
    await this.runEdit(async () => {
      try {
        await this.projects.assignDanceMember(detail.projectId, request);
        if (this.detail()?.projectId !== detail.projectId) return;
        await this.load(detail.projectId, { keepSelectedClip: true, quietErrors: true, onlyIfCurrent: true });
        if (this.detail()?.projectId !== detail.projectId) return;
        const projectId = detail.projectId;
        const ref = this.snackBar.open(
          `${request.sourcePersonId}의 클립을 ${request.memberName}로 합쳤습니다`,
          '실행취소',
          { duration: 6000 },
        );
        ref.onAction().subscribe(() => {
          void this.undoDanceAssignment(projectId, request.sourcePersonId);
        });
      } catch (err) {
        this.notify.showToast(appErrorFrom(err));
      }
    });
  }

  /**
   * 실행취소 — nest 신설 해제 엔드포인트를 부르고 상세를 다시 받는다. 이 배치에서
   * 병행 작업 중이라 엔드포인트가 아직 없을 수 있다 — 실패는 기존 에러 처리로 흘린다.
   */
  private async undoDanceAssignment(projectId: string, sourcePersonId: string): Promise<void> {
    await this.enqueueEdit(async () => {
      try {
        await this.projects.deleteDanceMemberAssignment(projectId, sourcePersonId);
        if (this.detail()?.projectId === projectId) await this.load(projectId, { onlyIfCurrent: true, quietErrors: true });
      } catch (err) {
        this.notify.showToast(appErrorFrom(err));
      }
    });
  }

  /**
   * 클립 삭제 = 서버에 숨김 기록(파일은 남는다) → 조용한 새로고침 → 스낵바 「되돌리기」로
   * 숨김 해제. 되돌릴 수 있으니 확인 모달은 자식(dance-result-detail)의 가벼운 문구 하나로 끝낸다.
   */
  async hideDanceClip(clipId: string): Promise<void> {
    const detail = this.detail();
    if (!detail || this.zipping()) return;
    const projectId = detail.projectId;
    const done = await this.runEdit(async () => {
      try {
        await this.projects.hideDanceClip(projectId, clipId);
        if (this.detail()?.projectId === projectId) await this.load(projectId, { keepSelectedClip: true, quietErrors: true, onlyIfCurrent: true });
        return true;
      } catch (err) {
        this.notify.showToast(appErrorFrom(err));
        return false;
      }
    });
    if (!done) return;
    if (this.detail()?.projectId !== projectId) return;
    const ref = this.snackBar.open('클립을 삭제했습니다', '되돌리기', { duration: 6000 });
    ref.onAction().subscribe(() => {
      void this.undoDanceClipChange(projectId, () => this.projects.restoreDanceClip(projectId, clipId));
    });
  }

  /**
   * 클립 삭제·이동 되돌리기 — 복원 API는 늘 부른다(사용자가 되돌리라고 했다). 다만 그사이
   * 다른 프로젝트로 넘어갔으면 새로고침은 건너뛴다 — 지금 보는 화면을 옛 프로젝트로 덮어쓰지 않게.
   */
  private async undoDanceClipChange(projectId: string, restore: () => Promise<unknown>): Promise<void> {
    await this.enqueueEdit(async () => {
      try {
        await restore();
      } catch (err) {
        this.notify.showToast(appErrorFrom(err));
        return;
      }
      if (this.detail()?.projectId === projectId) await this.load(projectId);
    });
  }

  async moveDanceClips(selection: { clipIds: string[]; sourcePersonId: string; targetPersonId: string }): Promise<void> {
    const target = this.detail()?.persons.find(p => p.personId === selection.targetPersonId);
    await this.runDanceEdit(id => this.projects.applyDanceClipAction(id, { type: 'move', ...selection }),
      `클립 ${selection.clipIds.length}개를 ${target?.personName ?? selection.targetPersonId}(으)로 옮겼습니다`);
  }

  async hideDanceClips(clipIds: string[]): Promise<void> {
    if (!clipIds.length) return;
    await this.runDanceEdit(id => this.projects.applyDanceClipAction(id, { type: 'hide', clipIds }),
      `클립 ${clipIds.length}개를 삭제했습니다`);
  }

  async saveDanceRange(event: { clip: ProjectClipItem; range: ClipTrim }): Promise<void> {
    await this.runDanceEdit(id => this.projects.trimDanceClip(id, event.clip.clipId, event.range), '구간을 저장했습니다');
  }

  async restoreDanceRange(clipId: string): Promise<void> {
    await this.runDanceEdit(id => this.projects.restoreDanceClipRange(id, clipId), '원래 구간으로 복원했습니다');
  }

  private async runDanceEdit(save: (projectId: string) => Promise<unknown>, message: string): Promise<void> {
    const project = this.detail();
    if (project?.category !== 'dance' || this.zipping()) return;
    await this.runEdit(async () => {
      try {
        await save(project.projectId);
        if (this.detail()?.projectId !== project.projectId) return;
        await this.load(project.projectId, { keepSelectedClip: true, quietErrors: true, onlyIfCurrent: true });
        if (this.detail()?.projectId === project.projectId) this.snackBar.open(message, '닫기', { duration: 4000 });
      } catch (error) {
        this.notify.showToast(appErrorFrom(error));
      }
    });
  }

  async downloadSelectedDanceZip(selection: { personId: string; clipIds: string[] }): Promise<void> {
    const project = this.detail();
    if (project?.category !== 'dance' || this.zipping() || this.editing() || !selection.clipIds.length) return;
    this.zipping.set(true);
    try {
      const url = await this.projects.selectedDanceZipUrl(project.projectId, selection.personId, selection.clipIds);
      await this.saveZip(url, project.title, selection.clipIds.length);
    } catch (error) {
      this.notify.showToast(appErrorFrom(error));
    } finally {
      this.zipping.set(false);
    }
  }

  closeClipOverlay(): void {
    this.clipOverlayId.set(null);
    this.clipOverlayIds.set([]);
  }

  showPreviousOverlayClip(): void {
    this.moveOverlayClip(-1);
  }

  showNextOverlayClip(): void {
    this.moveOverlayClip(1);
  }

  /**
   * 전체 ZIP 저장. 스트리밍이라 총량을 몰라 퍼센트 없이 스피너만 띄운다(spec §4.2).
   * 같은 버튼이 자리를 지킨 채 비활성 → 중복 클릭도 함께 막힌다.
   */
  async downloadAllZip(personId: string | null = null): Promise<void> {
    const project = this.detail();
    if (!project || this.zipping()) return;
    const url = this.projects.projectZipUrl(project.projectId, personId);
    if (!url) return;

    this.zipping.set(true);
    try {
      const count = personId
        ? (project.clips ?? []).filter((clip) => canExportClip(project, clip) &&
            (clip.personIds?.includes(personId) || clip.personId === personId)).length
        : this.zipCount();
      await this.saveZip(url, project.title, count);
    } catch (err) {
      this.notify.showToast(appErrorFrom(err));
    } finally {
      this.zipping.set(false);
    }
  }

  async downloadSelectedPersonZip(selection: { personId: string; clipIds: string[] }): Promise<void> {
    const project = this.detail();
    if (!project || project.category !== 'person' || this.zipping() || !selection.clipIds.length) return;
    this.zipping.set(true);
    try {
      const url = await this.projects.selectedPersonZipUrl(project.projectId, selection.personId, selection.clipIds);
      await this.saveZip(url, project.title, selection.clipIds.length);
    } catch (err) {
      this.notify.showToast(appErrorFrom(err));
    } finally {
      this.zipping.set(false);
    }
  }

  private async saveZip(url: string, title: string, count: number): Promise<void> {
    const base = safeFilePart(title, 'project');
    const result = await this.fileDownload.save(url, `${base}-${fileTimestamp(new Date())}.zip`);
    if (result.status === 'completed') {
      this.snackBar.open(`${count}개 클립을 저장했습니다`, '닫기', { duration: 4000 });
    } else {
      this.notifyIfInterrupted(result);
    }
  }

  /**
   * 클립 구간 저장. 성공하면 **상세를 통째로 다시 불러온다** — 응답 클립만 갈아끼우면
   * 재생이 403으로 깨진다. 영상 URL은 `?path=…&mediaToken=…` 형태이고 티켓은 경로마다
   * 발급되는데, 자르고 나면 경로가 `clip_NN_edit.mp4`로 바뀌어 그 경로의 티켓이 없다.
   * `load()`가 티켓 발급까지 도맡으므로 그대로 다시 부른다.
   */
  async onTrimSave(event: { clip: ProjectClipItem; range: ClipTrim }): Promise<void> {
    const project = this.detail();
    if (!project || this.trimmingClipId()) return;

    this.trimmingClipId.set(event.clip.clipId);
    try {
      // 손잡이가 양 끝이면 되돌리기다. 길이 비교를 서버로 넘기면 화면(manifest 구간)과
      // 서버(ffprobe 실측)의 오차에 걸리므로, 판정은 여기서 하고 별도 동작으로 보낸다.
      // 기본값을 0으로 두면 원본 길이를 모를 때 **모든 저장이 되돌리기가 된다.**
      const originalDurationSec = event.clip.originalDurationSec;
      const reverting = typeof originalDurationSec === 'number'
        && event.range.startSec <= 0
        && event.range.endSec >= originalDurationSec;

      if (reverting) {
        await this.projects.revertClipTrim(project.projectId, event.clip.clipId);
      } else {
        await this.projects.trimClip(project.projectId, event.clip.clipId, event.range);
      }

      // 상세를 다시 받으면 같은 경로라도 mediaToken이 새로 발급돼 `src` 문자열이 바뀐다 →
      // 플레이어가 리로드되며 재생 위치를 잃는다. 트리머는 열린 채이므로 위치를 되살려 준다.
      const keepAtSec = this.trimmedPlayheadFor(event);
      await this.load(project.projectId, { keepSelectedClip: true });
      // load()는 실패를 삼키고 detail을 비운다 — 그 위에 성공 스낵바를 띄우면
      // "불러오지 못했습니다" 화면에 대고 저장됐다고 말하는 꼴이 된다.
      if (!this.detail()) return;

      this.restoreSeek.set({ sec: keepAtSec, seq: ++this.restoreSeq });
      this.snackBar.open(reverting ? '원본으로 되돌렸습니다' : '저장했습니다', '닫기', { duration: 4000 });
    } catch (err) {
      this.notify.showToast(appErrorFrom(err));
    } finally {
      this.trimmingClipId.set(null);
    }
  }

  /** 저장 뒤 플레이어를 되돌려 놓을 위치. 잘라낸 구간의 시작이 가장 자연스럽다. */
  private trimmedPlayheadFor(event: { range: ClipTrim }): number {
    return Math.max(0, event.range.startSec);
  }

  /** 개별 클립·렌더 저장. URL은 이미 mediaToken이 붙어 있다(withMediaUrls). */
  async downloadFile(url: string, title: string): Promise<void> {
    try {
      const result = await this.fileDownload.save(url, `${safeFilePart(title, 'clip')}.mp4`);
      if (result.status === 'completed') {
        this.snackBar.open('저장했습니다', '닫기', { duration: 4000 });
      } else {
        this.notifyIfInterrupted(result);
      }
    } catch (err) {
      this.notify.showToast(appErrorFrom(err));
    }
  }

  async downloadPersonClip(clip: ProjectClipItem): Promise<void> {
    const project = this.detail();
    if (project?.category !== 'person' || clip.excluded) return;
    const url = this.projects.projectPersonClipUrl(project.projectId, clip.clipId);
    if (!url) return;
    await this.downloadFile(url, clip.title);
  }

  /**
   * 저장 실패(interrupted)만 토스트로 알린다. Electron 브리지는 저장 실패를 예외가 아니라
   * `{status:'interrupted'}`로 돌려주므로(ZIP 404·스트리밍 오류·디스크 부족 등) 그냥 두면
   * 화면에 아무 신호도 없이 조용히 끝난다. cancelled(사용자가 스스로 취소)는 계속 무음.
   */
  private notifyIfInterrupted(result: FileSaveResult): void {
    if (result.status !== 'interrupted') return;
    this.notify.showToast({ category: 'internal', message: '다운로드에 실패했습니다. 다시 시도해주세요.' });
  }

  async confirmDelete(): Promise<void> {
    const project = this.detail();
    if (!project) return;
    const approved = await this.confirmDialog.confirm({
      title: '이 프로젝트를 삭제할까요?',
      message: project.category === 'person'
        ? `「${project.title}」의 분석 결과와 보관된 원본 영상이 삭제됩니다. 등장 장면 ${this.zipCount()}개의 구간 정보도 사라집니다. 되돌릴 수 없습니다.`
        : `「${project.title}」의 클립 ${this.zipCount()}개와 결과 영상이 디스크에서 함께 삭제됩니다. 되돌릴 수 없습니다.`,
      confirmLabel: '삭제',
      danger: true,
    });
    if (!approved) return;

    try {
      await this.jobs.deleteArchiveEntry(project.jobId);
    } catch (err) {
      this.notify.showToast(appErrorFrom(err));
      return;
    }
    await this.router.navigate(['/projects']);
    // 보관함으로 돌아간 뒤에도 남는다(MatSnackBar는 앱 레벨) — 되돌릴 수 없는 동작의 완료 신호.
    this.snackBar.open('삭제했습니다', '닫기', { duration: 4000 });
  }

  /**
   * `quietErrors`: 실패해도 상세·에러를 건드리지 않고 그대로 던진다(백그라운드 폴링용 —
   * 호출부가 기록·재시도를 맡는다).
   */
  private async load(
    projectId: string,
    options: { keepSelectedClip?: boolean; quietErrors?: boolean; onlyIfCurrent?: boolean } = {},
  ): Promise<void> {
    // 이미 상세를 한 번 받은 뒤의 재호출(트리머 저장·인물 배정·배정 취소 후 새로고침)은
    // loading을 안 건드린다 — 건드리면 템플릿의 `@if (loading())`가 잠깐 true였다 false로
    // 돌아오며 결과 화면(app-dance-result-detail/app-dialog-result-detail)을 통째로
    // 다시 만든다. 그 안의 HighlightShortformDraft 설정, 안무 클립 체크 상태가 그렇게
    // 날아간다 — 최초 로드(detail이 아직 없음)만 로딩 화면을 보여준다.
    const silent = this.detail() !== null;
    if (!silent) this.loading.set(true);
    if (!options.quietErrors) this.error.set(null);
    try {
      const detail = await this.projects.getDetail(projectId);
      if (options.onlyIfCurrent && this.detail()?.projectId !== projectId) return;
      if (detail.category === 'storyboard') {
        const batchId = detail.result?.['storyboardBatchId'];
        if (typeof batchId !== 'string' || !batchId.trim()) throw new Error('스토리보드 결과를 찾지 못했습니다.');
        await this.router.navigate(['/shortform/director/batches', batchId], { replaceUrl: true });
        return;
      }
      this.detail.set(detail);
      // 저장 후 새로고침이면 보던 클립을 그대로 둔다 — 첫 클립으로 튀면 트리머가 닫히고
      // (클립 id가 바뀌므로) 방금 자른 결과를 확인할 자리를 잃는다.
      const keepId = this.selectedClipId();
      const stillThere = options.keepSelectedClip
        && !!keepId
        && detail.clips.some((clip) => clip.clipId === keepId)
        && (!['person', 'dance'].includes(detail.category) || this.visiblePersons().some((person) =>
          person.personId === this.selectedPersonId() && person.clipIds.includes(keepId)));
      if (!stillThere) this.selectDefaultMedia(detail);
    } catch (err) {
      if (options.quietErrors) throw err;
      this.detail.set(null);
      this.error.set(err instanceof Error ? err.message : '프로젝트 결과를 불러오지 못했습니다.');
    } finally {
      if (!silent) this.loading.set(false);
    }
  }

  /**
   * 폴링 한 번 — 앞 요청이 아직이거나 구간 저장 중(그쪽이 알아서 다시 부른다)이면 건너뛴다.
   * 실패는 **조용히** 넘긴다: 지금 상세·에러를 건드리면 결과 화면이 내려가며 Draft(클립별
   * 타이틀·템플릿·BGM·출처)가 사라진다. 기록만 하고 다음 틱에 다시 묻고, 연달아
   * `RAW_CLIP_POLL_MAX_FAILURES`번 실패하면 멈추고 스낵바로만 알린다.
   */
  private async pollRawClips(projectId: string): Promise<void> {
    if (this.rawClipPollInFlight || this.trimmingClipId()) return;
    if (this.detail()?.projectId !== projectId) return;
    this.rawClipPollInFlight = true;
    try {
      await this.load(projectId, { keepSelectedClip: true, quietErrors: true });
      this.rawClipPollFailures = 0;
    } catch (err) {
      this.rawClipPollFailures += 1;
      this.logger.log(
        'warn',
        `raw clip poll failed: ${err}`,
        { projectId, failures: this.rawClipPollFailures },
        'projects-detail|raw-clip-poll',
      );
      if (this.rawClipPollFailures >= RAW_CLIP_POLL_MAX_FAILURES) {
        this.rawClipPollStopped.set(true);
        this.snackBar.open('원본 비율 클립 상태를 확인하지 못했어요', '닫기', { duration: 6000 });
      }
    } finally {
      this.rawClipPollInFlight = false;
    }
  }

  /**
   * 숏폼 카드 [편집] 복원(T13) — 그 작업의 요청 원본으로 인물/클립 선택을 되돌리고, 체크·설정은
   * `shortformRestore`로 결과 화면에 넘긴다. 못 찾거나 이 프로젝트 것이 아니면 조용히 넘긴다(기록만).
   * 어느 경우든 쿼리는 지운다 — 새로고침·뒤로가기로 다시 덮어쓰지 않게.
   */
  private async restoreFromShortform(jobId: string): Promise<void> {
    await this.restoreAction.run(() => this.restoreFromShortformNow(jobId));
  }

  private async restoreFromShortformNow(jobId: string): Promise<void> {
    try {
      const detail = this.detail();
      if (!detail) return;
      const request = await this.shortformRequestFor(jobId);
      if (!request) {
        this.logShortformRestore('shortform restore skipped: request not found', { jobId });
        return;
      }
      if (request.origin.projectId !== detail.projectId || request.origin.kind !== detail.category) {
        this.logShortformRestore('shortform restore skipped: origin mismatch', {
          jobId, projectId: detail.projectId, originProjectId: request.origin.projectId,
        });
        return;
      }
      const clipIds = this.selectShortformOrigin(detail, request);
      if (clipIds.length < request.clipIds.length) {
        const message = clipIds.length === 0
          ? SHORTFORM_RESTORE_SETTINGS_ONLY_MESSAGE
          : SHORTFORM_RESTORE_PARTIAL_MESSAGE;
        this.snackBar.open(message, '닫기', { duration: 4000 });
      }
      this.shortformRestore.set({ clipIds, settings: request.settings });
    } catch (err) {
      this.logShortformRestore(`shortform restore failed: ${err}`, { jobId });
    } finally {
      void this.router.navigate([], {
        relativeTo: this.route,
        queryParams: { fromShortform: null },
        queryParamsHandling: 'merge',
        replaceUrl: true,
      });
    }
  }

  /**
   * 요청 원본 찾기: ① 완료된 작업의 프로젝트 스냅샷 params(`render_manifest`) → ② 그 렌더
   * 프로젝트의 manifest → ③ 아직 프로젝트가 아닌 작업(대기·렌더 중·실패)은 작업 목록의 params.
   */
  private async shortformRequestFor(jobId: string): Promise<SavedHighlightShortform | null> {
    const fromParams = (params: Record<string, unknown> | undefined) =>
      highlightShortformRequestFromManifest(params?.['render_manifest']);
    try {
      const snapshot = await this.projects.getByJob(jobId);
      const request = fromParams(snapshot.params)
        ?? highlightShortformRequestFromManifest(await this.projects.getManifest(snapshot.projectId));
      if (request) return request;
    } catch {
      // 아직 프로젝트가 아니다(404) — 작업 목록에서 찾는다.
    }
    return fromParams(this.jobs.jobs().find((job) => job.jobId === jobId)?.params);
  }

  /** 인물(안무)·클립(대사)을 고르고, 지금 상세에 남아 있는 복원 대상 클립 id를 돌려준다. */
  private selectShortformOrigin(detail: ProjectDetail, request: SavedHighlightShortform): string[] {
    const present = new Set(detail.clips.map((clip) => clip.clipId));
    if (detail.category === 'dance' || detail.category === 'person') {
      const person = this.visiblePersons().find((item) => item.personId === request.origin.personId);
      if (!person) return [];
      this.selectedPersonId.set(person.personId);
      const own = new Set(person.clipIds);
      const available = new Set(detail.clips.filter((clip) => !clip.excluded).map((clip) => clip.clipId));
      const restored = request.clipIds.filter((id) => own.has(id) && present.has(id) && available.has(id));
      if (detail.category === 'person') {
        this.selectedClipId.set(restored[0] ?? person.clipIds.find((id) => available.has(id)) ?? null);
      }
      return restored;
    }
    const clipId = request.clipIds[0];
    if (!clipId || !present.has(clipId)) return [];
    this.selectedClipId.set(clipId);
    return [clipId];
  }

  private logShortformRestore(message: string, ctx: Record<string, unknown>): void {
    this.logger.log('warn', message, ctx, 'projects-detail|shortform-restore');
  }

  private selectDefaultMedia(detail: ProjectDetail): void {
    if (detail.category === 'person') {
      const persons = visiblePersonCandidates(detail);
      const chosen = persons.find((person) => person.personId === this.selectedPersonId()) ?? persons[0];
      this.selectedPersonId.set(chosen?.personId ?? null);
      const ids = new Set(chosen?.clipIds ?? []);
      this.selectedClipId.set(detail.clips.find((clip) => ids.has(clip.clipId) && !clip.excluded)?.clipId
        ?? detail.clips.find((clip) => ids.has(clip.clipId))?.clipId ?? null);
      return;
    }
    if (detail.category === 'dance') {
      // 새로고침(클립 삭제·이동·되돌리기) 뒤에도 고른 인물이 인물 칸에 남아 있으면 그대로 둔다 —
      // 기본 인물로 튀면 ② 체크 상태를 보던 자리를 잃는다. 사라졌으면 기본 인물로(비워 두지 않는다).
      const persons = visibleDancePersons(detail.persons);
      const keepId = this.selectedPersonId();
      const kept = !!keepId && persons.some((person) => person.personId === keepId);
      if (!kept) this.selectedPersonId.set(defaultDancePerson(persons)?.personId ?? null);
      this.selectedClipId.set(null);
      return;
    }
    const firstClip = detail.clips.find((clip) => !!clip.videoUrl) ?? detail.clips[0] ?? null;
    this.selectedClipId.set(firstClip?.clipId ?? null);
    this.selectedPersonId.set(null);
  }

  private moveOverlayClip(offset: number): void {
    const clipIds = this.clipOverlayIds();
    const currentClipId = this.clipOverlayId();
    if (!currentClipId || clipIds.length === 0) return;

    const currentIndex = Math.max(0, clipIds.indexOf(currentClipId));
    const nextIndex = (currentIndex + offset + clipIds.length) % clipIds.length;
    this.clipOverlayId.set(clipIds[nextIndex]);
  }
}

/** Show every identified candidate with at least one visible scene. */
function visiblePersonCandidates(detail: ProjectDetail): ProjectPersonItem[] {
  const visibleIds = new Set(detail.clips.filter((clip) => !clip.excluded).map((clip) => clip.clipId));
  return sortPersonCandidates(detail.persons.filter((person) => !person.unclassified && person.personId !== 'unidentified' &&
    person.clipIds.some((id) => visibleIds.has(id))), visibleIds);
}

/**
 * ① 인물 칸 표시 규칙(T12 D12) — 확정 멤버는 늘, 익명은 클립 2개 이상이거나 (확정 멤버가
 * 있을 때) 1개 이상. 함께 등장 배정 대기와 미분류는 숨긴다. 정렬 = 확정 → 익명
 * (각 묶음 안은 원래 순서).
 */
function visibleDancePersons(persons: ProjectPersonItem[]): ProjectPersonItem[] {
  const hasMapped = persons.some((person) => person.mappedMember === true);
  const mapped = persons.filter((person) => !person.sharedReview && !person.unclassified && person.mappedMember === true);
  const anonymous = persons.filter((person) =>
    !person.sharedReview &&
    person.mappedMember !== true &&
    !person.unclassified &&
    (person.clipIds.length > 1 || (hasMapped && person.clipIds.length > 0)));
  return [...mapped, ...anonymous];
}

/** 기본 선택 = 클립 있는 첫 확정 멤버 → 클립 있는 첫 인물 → (전부 0개면) 첫 행.
 *  보이는 행이 있는 한 선택을 비워 두지 않는다. */
function defaultDancePerson(persons: ProjectPersonItem[]): ProjectPersonItem | null {
  return persons.find((person) => person.mappedMember === true && person.clipIds.length > 0)
    ?? persons.find((person) => person.clipIds.length > 0)
    ?? persons[0]
    ?? null;
}

function canExportClip(project: ProjectDetail, clip: ProjectClipItem): boolean {
  return !clip.excluded && (project.category === 'person' || !!clip.videoPath ||
    (project.category === 'dance' && !!project.sourceVideoPath &&
      typeof clip.sourceStartSec === 'number' && Number.isFinite(clip.sourceStartSec) && clip.sourceStartSec >= 0 &&
      typeof clip.sourceEndSec === 'number' && Number.isFinite(clip.sourceEndSec) && clip.sourceEndSec > clip.sourceStartSec));
}
