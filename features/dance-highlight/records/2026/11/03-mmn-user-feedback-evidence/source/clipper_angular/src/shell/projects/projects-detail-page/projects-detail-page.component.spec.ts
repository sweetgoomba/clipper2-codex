import { provideZonelessChangeDetection, signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { ActivatedRoute, Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Clipboard } from '@angular/cdk/clipboard';
import { EMPTY, Subject } from 'rxjs';
import { BackendLocator, JobHistoryService, ProjectDetail, ProjectHistoryService, ProjectPersonItem, VIEWPORT_PROBE } from '@core';
import { MediaLibraryStore } from '@core/media-library/media-library.store';
import { NavHistoryService } from '@core/navigation/nav-history.service';
import {
  CUT_TRANSITION_EFFECTS,
  type HighlightShortformSettings,
} from '@features/highlight-shortform/models/highlight-shortform';
import { HighlightShortformApi } from '@features/highlight-shortform/services/highlight-shortform-api';
import { HighlightShortformCatalogService } from '@features/highlight-shortform/services/highlight-shortform-catalog.service';
import { TemplatePreviewFontLoader } from '@shared/template-runtime/template-preview-font.service';

/** 안무/대사 결과 화면(HighlightShortformDraft)이 BGM을 소재함(media library)에서 고르게
 *  되면서 이 스토어를 직접 inject한다 — 진짜 백엔드를 안 태우게 가짜로 채운다. */
function fakeMediaLibraryStore() {
  return {
    assets: signal([]),
    loaded: signal(true),
    error: signal(null),
    load: jasmine.createSpy('load').and.resolveTo(undefined),
    assetUrl: (p: string) => `http://127.0.0.1:1/media/${p}`,
  };
}
import { ConfirmDialogService } from '../../../shared/ui/confirm-dialog/confirm-dialog.service';
import { FileDownloadService } from '../../../core/download/file-download.service';
import { ErrorNotificationService } from '../../../core/errors/error-notification.service';
import { appErrorFrom } from '../../../core/errors/app-error';
import { RendererLogger } from '../../../core/logging/renderer-logger';
import { DanceResultDetailComponent } from '../dance-result-detail/dance-result-detail.component';
import { PersonResultDetailComponent } from '../person-result-detail/person-result-detail.component';
import { ProjectsDetailPageComponent } from './projects-detail-page.component';

/** 액션을 인라인 한 줄로 유지시키는 뷰포트 고정. 실측(size)이 아니라 forced를 줘야
 *  BreakpointService의 effect가 뒤이어 다시 덮어쓰지 않는다(logs.component.spec.ts와 같은 관습). */
function forcedLargeProbe() {
  return {
    size: () => ({ width: 0, height: 0 }),
    forcedWidth: () => 'large' as const,
    forcedHeight: () => 'expanded' as const,
  };
}

describe('ProjectsDetailPageComponent', () => {
  let fixture: ComponentFixture<ProjectsDetailPageComponent>;
  let projects: {
    applyDanceClipAction: jasmine.Spy;
    trimDanceClip: jasmine.Spy;
    restoreDanceClipRange: jasmine.Spy;
    selectedDanceZipUrl: jasmine.Spy;
    projectDanceClipUrl: jasmine.Spy;
    getDetail: jasmine.Spy;
    editPerson: jasmine.Spy;
    assignDanceMember: jasmine.Spy;
    deleteDanceMemberAssignment: jasmine.Spy;
    hideDanceClip: jasmine.Spy;
    restoreDanceClip: jasmine.Spy;
    assignDanceClip: jasmine.Spy;
    unassignDanceClip: jasmine.Spy;
    projectZipUrl: jasmine.Spy;
    selectedPersonZipUrl: jasmine.Spy;
    projectPersonClipUrl: jasmine.Spy;
    trimClip: jasmine.Spy;
    revertClipTrim: jasmine.Spy;
    getByJob: jasmine.Spy;
    getManifest: jasmine.Spy;
  };
  let confirmDialog: {
    confirm: jasmine.Spy;
  };
  let jobs: {
    deleteArchiveEntry: jasmine.Spy;
    jobs: ReturnType<typeof signal<unknown[]>>;
  };
  let notify: {
    showToast: jasmine.Spy;
    showSuccess: jasmine.Spy;
    showTransientMessage: jasmine.Spy;
  };
  let clipboard: { copy: jasmine.Spy };
  let download: {
    save: jasmine.Spy;
  };
  let snackBar: {
    open: jasmine.Spy;
  };
  let router: {
    navigate: jasmine.Spy;
  };
  let navBack: jasmine.Spy;
  let routeParams: Record<string, string>;
  let routeQuery: Record<string, string>;

  const danceDetail: ProjectDetail = {
    projectId: 'project-dance',
    jobId: 'job-dance',
    pluginName: 'dance_highlight',
    status: 'completed',
    title: 'Dance highlight',
    sourceVideoPath: null,
    outputRoot: '/tmp/project-dance',
    params: {},
    result: {},
    artifacts: [],
    createdAt: '2026-07-01T00:00:00.000Z',
    updatedAt: '2026-07-01T00:00:00.000Z',
    completedAt: '2026-07-01T00:00:00.000Z',
    category: 'dance',
    clips: [],
    persons: [],
    renders: [],
  };

  /** ZIP 관련 테스트용: videoPath가 있는 클립 2개(각 다른 person) + videoPath 없는 클립 1개(zipCount에서 제외되어야 함). */
  const detailWithClips: ProjectDetail = {
    ...danceDetail,
    clips: [
      { clipId: 'c1', title: 'clip 1', durationSec: 3, videoPath: '/tmp/c1.mp4', personId: 'person_1' },
      { clipId: 'c2', title: 'clip 2', durationSec: 3, videoPath: '/tmp/c2.mp4', personId: 'person_2' },
      { clipId: 'c3', title: 'clip 3 (영상 없음)', durationSec: 3, personId: 'person_1' },
    ],
  };

  const legacyStoryboardDetail: ProjectDetail = {
    ...danceDetail,
    projectId: 'project-storyboard-legacy',
    jobId: 'job-storyboard-legacy',
    pluginName: 'shortform_director',
    title: 'Archived storyboard render',
    category: 'shortform_director',
    renders: [{
      renderId: 'render-legacy-1',
      title: 'Completed storyboard video',
      durationSec: 18,
      videoUrl: 'data:video/mp4;base64,AAAA',
      completedAt: '2026-08-24T00:00:00.000Z',
      active: true,
    }],
  };

  describe('Dance source range and batch actions', () => {
    const scene = { clipId: 'main_0000', title: 'scene', durationSec: 4,
      sourceStartSec: 10, sourceEndSec: 14, personId: 'person_1', personIds: ['person_1', 'sakura'] };
    const sourceDetail: ProjectDetail = { ...danceDetail, sourceVideoPath: 'diagnostics/source.mp4',
      sourceVideoUrl: 'data:video/mp4;base64,AA', sourceDurationSec: 60, clips: [scene],
      persons: [{ personId: 'person_1', clipIds: [scene.clipId] },
        { personId: 'sakura', mappedMember: true, clipIds: [scene.clipId] }] };
    function prepare(): any {
      fixture.componentInstance.detail.set(sourceDetail);
      fixture.componentInstance.selectedPersonId.set('person_1');
      projects.getDetail.and.resolveTo(sourceDetail);
      return fixture.componentInstance;
    }
    it('counts source-only scenes and all shared recipients for ZIP', async () => {
      const page = prepare();
      expect(page.zipCount()).toBe(1);
      projects.projectZipUrl.and.returnValue('data:application/zip;base64,AA');
      await page.downloadAllZip('sakura');
      expect(snackBar.open).toHaveBeenCalledWith('1개 클립을 저장했습니다', '닫기', jasmine.any(Object));
    });
    it('saves absolute range metadata then reloads the same scene', async () => {
      const page = prepare();
      page.selectedClipId.set(scene.clipId);
      await page.saveDanceRange?.({ clip: scene, range: { startSec: 9, endSec: 15 } });
      expect(projects.trimDanceClip).toHaveBeenCalledOnceWith('project-dance', scene.clipId, { startSec: 9, endSec: 15 });
      expect(projects.trimClip).not.toHaveBeenCalled();
      expect(page.selectedClipId()).toBe(scene.clipId);
    });
    it('sends one atomic move with the selected source recipient', async () => {
      const page = prepare();
      const move = { clipIds: [scene.clipId], sourcePersonId: 'person_1', targetPersonId: 'sakura' };
      await page.moveDanceClips?.(move);
      expect(projects.applyDanceClipAction).toHaveBeenCalledOnceWith('project-dance', { type: 'move', ...move });
      expect(projects.assignDanceClip).not.toHaveBeenCalled();
    });
    it('uses scoped selection export even without prebuilt MP4', async () => {
      const page = prepare();
      await page.downloadSelectedDanceZip?.({ personId: 'person_1', clipIds: [scene.clipId] });
      expect(projects.selectedDanceZipUrl).toHaveBeenCalledOnceWith('project-dance', 'person_1', [scene.clipId]);
      expect(download.save).toHaveBeenCalled();
    });
    it('does not refresh the old project after an in-flight batch completes', async () => {
      const page = prepare();
      let resolve!: (value: unknown) => void;
      projects.applyDanceClipAction.and.returnValue(new Promise(r => { resolve = r; }));
      const pending = page.hideDanceClips?.([scene.clipId]);
      expect(projects.applyDanceClipAction).toHaveBeenCalledOnceWith('project-dance', { type: 'hide', clipIds: [scene.clipId] });
      page.detail.set({ ...sourceDetail, projectId: 'new-project' });
      resolve?.(sourceDetail);
      await pending;
      expect(projects.getDetail).not.toHaveBeenCalled();
      expect(page.detail().projectId).toBe('new-project');
    });
  });

  it('redirects a stored storyboard project to the batch viewer without opening video media', async () => {
    projects.getDetail.and.resolveTo({ ...danceDetail, category: 'storyboard', pluginName: 'shortform_director', result: { kind: 'storyboard-batch', storyboardBatchId: 'b1' } });
    await (fixture.componentInstance as any).load('project-storyboard');
    expect(router.navigate).toHaveBeenCalledWith(['/shortform/director/batches', 'b1'], { replaceUrl: true });
  });

  beforeEach(async () => {
    projects = {
      applyDanceClipAction: jasmine.createSpy('applyDanceClipAction').and.resolveTo(danceDetail),
      trimDanceClip: jasmine.createSpy('trimDanceClip').and.resolveTo(danceDetail),
      restoreDanceClipRange: jasmine.createSpy('restoreDanceClipRange').and.resolveTo(danceDetail),
      selectedDanceZipUrl: jasmine.createSpy('selectedDanceZipUrl').and.resolveTo('data:application/zip;base64,AA'),
      projectDanceClipUrl: jasmine.createSpy('projectDanceClipUrl').and.returnValue('data:video/mp4;base64,AA'),
      getDetail: jasmine.createSpy('getDetail').and.resolveTo(danceDetail),
      editPerson: jasmine.createSpy('editPerson').and.resolveTo(undefined),
      assignDanceMember: jasmine.createSpy('assignDanceMember').and.resolveTo(danceDetail),
      deleteDanceMemberAssignment: jasmine.createSpy('deleteDanceMemberAssignment').and.resolveTo(danceDetail),
      hideDanceClip: jasmine.createSpy('hideDanceClip').and.resolveTo(danceDetail),
      restoreDanceClip: jasmine.createSpy('restoreDanceClip').and.resolveTo(danceDetail),
      assignDanceClip: jasmine.createSpy('assignDanceClip').and.resolveTo(danceDetail),
      unassignDanceClip: jasmine.createSpy('unassignDanceClip').and.resolveTo(danceDetail),
      projectZipUrl: jasmine.createSpy('projectZipUrl').and.returnValue(null),
      selectedPersonZipUrl: jasmine.createSpy('selectedPersonZipUrl').and.resolveTo('http://x/selected.zip'),
      projectPersonClipUrl: jasmine.createSpy('projectPersonClipUrl').and.returnValue(null),
      trimClip: jasmine.createSpy('trimClip').and.resolveTo(undefined),
      revertClipTrim: jasmine.createSpy('revertClipTrim').and.resolveTo(undefined),
      getByJob: jasmine.createSpy('getByJob').and.rejectWith(new Error('Unknown project for job')),
      getManifest: jasmine.createSpy('getManifest').and.rejectWith(new Error('not found')),
    };
    routeParams = {};
    routeQuery = {};
    confirmDialog = {
      confirm: jasmine.createSpy('confirm').and.resolveTo(true),
    };
    jobs = {
      deleteArchiveEntry: jasmine.createSpy('deleteArchiveEntry').and.resolveTo(undefined),
      jobs: signal<unknown[]>([]),
    };
    notify = {
      showToast: jasmine.createSpy('showToast'),
      showSuccess: jasmine.createSpy('showSuccess'),
      showTransientMessage: jasmine.createSpy('showTransientMessage'),
    };
    clipboard = { copy: jasmine.createSpy('copy').and.returnValue(true) };
    download = {
      save: jasmine.createSpy('save').and.resolveTo({ status: 'completed' }),
    };
    snackBar = {
      // 반환값에 .onAction()이 필요한 호출부(assignDancePerson의 실행취소 배선)가 있어
      // 기본값도 MatSnackBarRef 흉내를 낸다 — 그 반환값을 쓰지 않는 다른 테스트는 그대로 동작한다.
      open: jasmine.createSpy('open').and.returnValue({ onAction: () => EMPTY }),
    };
    router = {
      navigate: jasmine.createSpy('navigate'),
    };
    navBack = jasmine.createSpy('navHistory.back');
    await TestBed.configureTestingModule({
      imports: [ProjectsDetailPageComponent],
      providers: [
        provideZonelessChangeDetection(),
        // 헤더 액션은 large 미만이면 ⋯ 메뉴로 접히고, 메뉴 콘텐츠는 열기 전까지 DOM에 없다
        // (page-header의 ACTIONS_OVERFLOW_THRESHOLD). Karma 창은 그 아래라 고정하지 않으면
        // [전체 다운로드]·[프로젝트 삭제]를 쿼리하는 아래 테스트가 전부 못 찾는다.
        { provide: VIEWPORT_PROBE, useValue: forcedLargeProbe() },
        {
          provide: ProjectHistoryService,
          useValue: projects,
        },
        {
          provide: JobHistoryService,
          useValue: jobs,
        },
        {
          provide: ActivatedRoute,
          // 기본은 projectId 없음(ngOnInit이 바로 에러로 끝남). 복원 테스트만 routeParams를 채운다.
          useValue: {
            snapshot: {
              paramMap: { get: (key: string) => routeParams[key] ?? null },
              queryParamMap: { get: (key: string) => routeQuery[key] ?? null },
            },
          },
        },
        {
          provide: Router,
          useValue: router,
        },
        { provide: NavHistoryService, useValue: { back: navBack } },
        {
          provide: ConfirmDialogService,
          useValue: confirmDialog,
        },
        {
          provide: FileDownloadService,
          useValue: download,
        },
        {
          provide: ErrorNotificationService,
          useValue: notify,
        },
        { provide: Clipboard, useValue: clipboard },
        {
          provide: MatSnackBar,
          useValue: snackBar,
        },
        {
          provide: HighlightShortformCatalogService,
          useValue: { listTemplates: () => Promise.resolve([]) },
        },
        { provide: MediaLibraryStore, useValue: fakeMediaLibraryStore() },
        { provide: RendererLogger, useValue: { log: jasmine.createSpy('log') } },
        { provide: HighlightShortformApi, useValue: { render: () => Promise.resolve({ jobId: 'j', projectId: 'p' }) } },
        { provide: BackendLocator, useValue: { getBaseUrl: () => Promise.resolve('http://nest') } },
        { provide: TemplatePreviewFontLoader, useValue: { fontFamilyCss: () => 'sans-serif' } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ProjectsDetailPageComponent);
  });


  describe('인물 편집 완료 알림과 선택 복구', () => {
    const personDetail: ProjectDetail = {
      ...danceDetail, category: 'person', pluginName: 'person_highlight',
      persons: [
        { personId: 'p1', personName: 'Person 1', personImageUrl: 'data:image/png;base64,AAAA', clipIds: ['c1', 'c2'] },
        { personId: 'p2', personName: '지상', personImageUrl: 'data:image/png;base64,AAAA', clipIds: ['c1'] },
      ],
      clips: [
        { clipId: 'c1', title: '공유 장면', durationSec: 3, personIds: ['p1', 'p2'], sourceStartSec: 1, sourceEndSec: 4 },
        { clipId: 'c2', title: '다음 장면', durationSec: 3, personIds: ['p1'], sourceStartSec: 5, sourceEndSec: 8 },
      ],
    };

    beforeEach(() => {
      fixture.componentInstance.detail.set(personDetail);
      fixture.componentInstance.selectedPersonId.set('p1');
      fixture.componentInstance.selectedClipId.set('c1');
      projects.getDetail.and.resolveTo(personDetail);
    });

    it('병합 저장이 완료된 뒤 원래 이름과 대상 이름을 스낵바로 알린다', async () => {
      let finish!: () => void;
      projects.editPerson.and.returnValue(new Promise<void>((resolve) => { finish = resolve; }));
      const component = fixture.componentInstance;
      const work = component.onPersonEdit({ type: 'merge', sourcePersonId: 'p1', targetPersonId: 'p2' });
      expect(snackBar.open).not.toHaveBeenCalled();
      await component.onPersonEdit({ type: 'merge', sourcePersonId: 'p1', targetPersonId: 'p2' });
      expect(projects.editPerson).toHaveBeenCalledTimes(1);
      projects.getDetail.and.resolveTo({ ...personDetail, persons: [personDetail.persons[1]] });
      finish();
      await work;
      expect(snackBar.open).toHaveBeenCalledOnceWith('인물 1 → 지상 병합 완료', '닫기', { duration: 4000 });
      expect(component.selectedPersonId()).toBe('p2');
      expect(component.editing()).toBeFalse();
    });

    it('장면 제거 후 공유 클립이 전체 결과에 남아 있어도 현재 인물의 다음 장면을 선택한다', async () => {
      const updated = { ...personDetail, persons: [
        { ...personDetail.persons[0], clipIds: ['c2'] }, personDetail.persons[1],
      ] };
      projects.getDetail.and.resolveTo(updated);
      const component = fixture.componentInstance;
      await component.onPersonEdit({ type: 'remove_clips', personId: 'p1', clipIds: ['c1'] });
      expect(component.selectedPersonId()).toBe('p1');
      expect(component.selectedClipId()).toBe('c2');
      expect(snackBar.open).toHaveBeenCalledOnceWith('인물 1에서 장면 1개를 제거했습니다', '닫기', { duration: 4000 });
    });

    it('인물 삭제 후 공유 장면이 남더라도 다음 인물을 선택한다', async () => {
      projects.getDetail.and.resolveTo({ ...personDetail, persons: [personDetail.persons[1]] });
      const component = fixture.componentInstance;
      await component.onPersonEdit({ type: 'delete_person', personId: 'p1' });
      expect(component.selectedPersonId()).toBe('p2');
      expect(component.selectedClipId()).toBe('c1');
      expect(snackBar.open).toHaveBeenCalledOnceWith('인물 1 삭제 완료', '닫기', { duration: 4000 });
    });

    it('이동한 장면 수와 목적지를 알린다', async () => {
      await fixture.componentInstance.onPersonEdit({ type: 'move_clips', sourcePersonId: 'p1', targetPersonId: 'p2', clipIds: ['c1', 'c2'] });
      expect(snackBar.open).toHaveBeenCalledOnceWith('장면 2개 → 지상 이동 완료', '닫기', { duration: 4000 });
    });

    it('저장 실패에는 성공 알림이나 선택 변경이 없다', async () => {
      projects.editPerson.and.rejectWith(new Error('save failed'));
      await fixture.componentInstance.onPersonEdit({ type: 'delete_person', personId: 'p1' });
      expect(snackBar.open).not.toHaveBeenCalled();
      expect(projects.getDetail).not.toHaveBeenCalled();
      expect(notify.showToast).toHaveBeenCalled();
      expect(fixture.componentInstance.selectedPersonId()).toBe('p1');
      expect(fixture.componentInstance.editing()).toBeFalse();
    });

    it('편집 요청부터 상세 재조회가 끝날 때까지 editing이 켜져 있고, 연타는 요청 한 번이다', async () => {
      const component = fixture.componentInstance;
      let finishReload!: (detail: ProjectDetail) => void;
      projects.getDetail.and.returnValue(new Promise<ProjectDetail>((resolve) => { finishReload = resolve; }));
      const work = component.onPersonEdit({ type: 'rename', personId: 'p1', name: '새 이름' });
      expect(component.editing()).toBeTrue();
      await Promise.resolve();
      await component.onPersonEdit({ type: 'rename', personId: 'p1', name: '새 이름' });
      await Promise.resolve();
      expect(component.editing()).toBeTrue(); // editPerson은 끝났어도 load()가 끝나기 전
      finishReload(personDetail);
      await work;
      expect(projects.editPerson).toHaveBeenCalledTimes(1);
      expect(component.editing()).toBeFalse();
    });

    it('편집 결과를 personEditOutcome으로 알린다 — 성공 true, 실패 false', async () => {
      const component = fixture.componentInstance;
      await component.onPersonEdit({ type: 'rename', personId: 'p1', name: 'a' });
      expect(component.personEditOutcome()).toEqual({ ok: true });
      projects.editPerson.and.rejectWith(new Error('save failed'));
      await component.onPersonEdit({ type: 'rename', personId: 'p1', name: 'b' });
      expect(component.personEditOutcome()).toEqual({ ok: false });
    });

    it('상세가 없어 일찍 돌아오거나 다른 편집이 진행 중이라 무시돼도 결과(false)는 반드시 온다', async () => {
      const component = fixture.componentInstance;
      component.detail.set(null);
      await component.onPersonEdit({ type: 'rename', personId: 'p1', name: 'a' });
      expect(component.personEditOutcome()).toEqual({ ok: false });

      component.detail.set(personDetail);
      let finish!: () => void;
      projects.editPerson.and.returnValue(new Promise<void>((resolve) => { finish = resolve; }));
      const first = component.onPersonEdit({ type: 'delete_person', personId: 'p2' });
      await Promise.resolve();
      const before = component.personEditOutcome();
      await component.onPersonEdit({ type: 'rename', personId: 'p1', name: 'c' });
      expect(component.personEditOutcome()).not.toBe(before);
      expect(component.personEditOutcome()).toEqual({ ok: false });
      finish();
      await first;
    });

    it('editing 동안 결과 화면의 편집 버튼이 잠긴다', async () => {
      const component = fixture.componentInstance;
      projects.editPerson.and.returnValue(new Promise<void>(() => undefined));
      routeParams = { projectId: personDetail.projectId };
      await component.ngOnInit();
      void component.onPersonEdit({ type: 'delete_person', personId: 'p1' });
      fixture.detectChanges();
      const child = fixture.debugElement.query(By.directive(PersonResultDetailComponent))
        .componentInstance as PersonResultDetailComponent;
      expect(child.actionsDisabled()).toBeTrue();
    });
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('안무 결과에서 판정 지도로 갔다가 결과로 돌아온다', () => {
    fixture.detectChanges();
    fixture.componentInstance.loading.set(false);
    fixture.componentInstance.error.set(null);
    fixture.componentInstance.detail.set(danceDetail);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('app-dance-result-detail')).not.toBeNull();
    expect(fixture.nativeElement.querySelector('app-dance-diagnostic-timeline')).toBeNull();
    const button = fixture.nativeElement.querySelector('[data-testid="dance-return-to-map"]') as HTMLButtonElement;
    expect(button).not.toBeNull();
    button.click();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('app-dance-diagnostic-timeline')).not.toBeNull();
    expect(fixture.nativeElement.querySelector('app-dance-result-detail')).toBeNull();
    (fixture.nativeElement.querySelector('[data-testid="dance-view-results"]') as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('app-dance-result-detail')).not.toBeNull();
  });

  it('헤더 뒤로가기 = 「뒤로」 — 홈 카드로 들어간 다른 화면들과 같은 이름', () => {
    fixture.detectChanges();
    const button = fixture.nativeElement.querySelector(
      '[data-testid="page-header-back"]',
    ) as HTMLButtonElement;

    // 아이콘 버튼이라 보이는 글자가 없다 — 이름은 aria-label/툴팁이 진다.
    expect(button.getAttribute('aria-label')).toBe('뒤로');
  });

  it('헤더 뒤로가기는 들어온 화면으로(없으면 홈) — 홈의 유형·정렬 필터가 그대로 돌아온다', () => {
    fixture.detectChanges();
    (fixture.nativeElement.querySelector('[data-testid="page-header-back"]') as HTMLButtonElement).click();

    expect(navBack).toHaveBeenCalledOnceWith(['/projects']);
    expect(router.navigate).not.toHaveBeenCalledWith(['/projects']);
  });

  it('안무 헤더 액션은 모든 클립 다운로드·프로젝트 삭제 둘뿐이다', () => {
    const component = fixture.componentInstance;
    fixture.detectChanges();
    component.error.set(null);
    component.detail.set(detailWithClips);
    fixture.detectChanges();

    const actions = fixture.nativeElement.querySelectorAll('.app-page-header__actions button');
    // textContent에는 Material Symbols의 리가처 글자(download/delete)가 섞인다 —
    // 아이콘 자리를 빼고 라벨만 본다.
    const labels = Array.from(actions, (button) => {
      const clone = (button as HTMLElement).cloneNode(true) as HTMLElement;
      clone.querySelectorAll('mat-icon').forEach((icon) => icon.remove());
      return clone.textContent?.trim();
    });
    expect(labels).toEqual(['모든 클립 다운로드', '프로젝트 삭제']);
  });

  describe('헤더 제목 = 모듈 이름, 부제 = 영상 제목', () => {
    const headerTitle = () =>
      (fixture.nativeElement.querySelector('.app-page-header h1') as HTMLElement).textContent?.trim();
    const headerSubtitle = () =>
      fixture.nativeElement.querySelector('[data-testid="page-header-subtitle"]') as HTMLElement | null;
    const longTitle = '[MV] 아티스트 - 곡 제목 (Official Video) #kpop #dance #shorts';

    it('안무 하이라이트 — 제목은 모듈 이름, 영상 제목은 부제(툴팁 포함)로 내려간다', () => {
      const component = fixture.componentInstance;
      fixture.detectChanges();
      component.error.set(null);
      component.detail.set({ ...detailWithClips, title: longTitle });
      fixture.detectChanges();

      expect(headerTitle()).toBe('안무 하이라이트');
      expect(headerSubtitle()?.textContent?.trim()).toBe(longTitle);
      expect(headerSubtitle()?.getAttribute('title')).toBe(longTitle);
    });

    it('안무 아티스트 배지를 기존 제목 구분선 오른쪽, 영상 제목 왼쪽에 둔다', () => {
      fixture.detectChanges();
      fixture.componentInstance.detail.set({
        ...detailWithClips,
        title: longTitle,
        params: { dance_setup: { artistName: 'Ive', artistDisplayName: '아이브 (Ive)' } },
      });
      fixture.detectChanges();

      const heading = fixture.nativeElement.querySelector('.app-page-header h1') as HTMLElement;
      const divider = heading.nextElementSibling as HTMLElement;
      const badge = divider.nextElementSibling as HTMLElement;
      expect(divider).toHaveClass('app-page-header__divider');
      expect(badge).toHaveClass('app-page-header__badge');
      expect(badge.textContent?.trim()).toBe('Ive (아이브)');
      expect(badge.nextElementSibling).toBe(headerSubtitle());
      expect(headerSubtitle()?.textContent?.trim()).toBe(longTitle);
    });

    it('옛 안무 결과는 저장된 아티스트명으로 표시하고, 아티스트 정보가 없으면 배지를 생략한다', () => {
      fixture.detectChanges();
      fixture.componentInstance.detail.set({ ...danceDetail, params: { dance_setup: { artistName: 'NewJeans' } } });
      fixture.detectChanges();
      expect((fixture.nativeElement.querySelector('.app-page-header__badge') as HTMLElement).textContent?.trim()).toBe('NewJeans');

      fixture.componentInstance.detail.set(danceDetail);
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('.app-page-header__badge')).toBeNull();
    });

    it('대사 하이라이트 — 제목은 모듈 이름이다', () => {
      const component = fixture.componentInstance;
      fixture.detectChanges();
      component.error.set(null);
      component.detail.set({ ...detailWithClips, pluginName: 'dialog_highlight', category: 'dialog', title: longTitle });
      fixture.detectChanges();

      expect(headerTitle()).toBe('대사 하이라이트');
      expect(headerSubtitle()?.textContent?.trim()).toBe(longTitle);
      expect(fixture.nativeElement.querySelector('.app-page-header__badge')).toBeNull();
    });

    it('상세가 없으면 폴백 제목만 두고 부제는 비운다', () => {
      fixture.detectChanges();

      expect(headerTitle()).toBe('프로젝트 결과');
      expect(headerSubtitle()).toBeNull();
    });

    for (const { category, pluginName, provenanceUrl } of [
      { category: 'dance' as const, pluginName: 'dance_highlight', provenanceUrl: true },
      { category: 'dialog' as const, pluginName: 'dialog_highlight', provenanceUrl: false },
      { category: 'person' as const, pluginName: 'person_highlight', provenanceUrl: true },
    ]) {
      it(`${category} 결과의 영상 제목 옆 링크 아이콘은 원본 URL을 복사하고 성공 스낵바를 띄운다`, () => {
        const url = 'https://www.youtube.com/watch?v=original';
        const provenance = 'https://youtu.be/original';
        fixture.detectChanges();
        fixture.componentInstance.detail.set({
          ...detailWithClips, category, pluginName,
          sourceAssets: [{
            type: 'video', originalInput: { type: 'youtube_url', url },
            provenance: { provider: 'yt_dlp', ...(provenanceUrl ? { originalUrl: provenance } : {}) },
          } as never],
        });
        fixture.detectChanges();

        const button = fixture.nativeElement.querySelector('[data-testid="page-header-subtitle-action"]') as HTMLButtonElement;
        expect(button).toBeTruthy();
        expect(button.previousElementSibling).toBe(headerSubtitle());
        expect(button.getAttribute('aria-label')).toBe('원본 URL 복사');
        expect(button.querySelector('mat-icon')?.textContent?.trim()).toBe('link');
        button.click();

        expect(clipboard.copy).toHaveBeenCalledOnceWith(provenanceUrl ? provenance : url);
        expect(notify.showSuccess).toHaveBeenCalledOnceWith('원본 URL을 복사했습니다.');
      });
    }

    it('로컬 파일 결과에는 원본 URL 복사 아이콘을 표시하지 않는다', () => {
      fixture.detectChanges();
      fixture.componentInstance.detail.set({
        ...detailWithClips,
        sourceAssets: [{
          type: 'video', originalInput: { type: 'local_file', path: '/tmp/source.mp4' },
          provenance: { provider: 'local' },
        } as never],
      });
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelector('[data-testid="page-header-subtitle-action"]')).toBeNull();
    });

    it('지원하지 않는 결과에는 원본 URL 복사 아이콘을 표시하지 않는다', () => {
      fixture.detectChanges();
      fixture.componentInstance.detail.set({
        ...detailWithClips, category: 'unknown', pluginName: 'other_plugin',
        sourceAssets: [{
          type: 'video', originalInput: { type: 'youtube_url', url: 'https://youtu.be/original' },
          provenance: { provider: 'yt_dlp' },
        } as never],
      });
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelector('[data-testid="page-header-subtitle-action"]')).toBeNull();
    });

    it('클립보드 복사가 실패하면 성공 알림 대신 실패를 알린다', () => {
      const url = 'https://www.youtube.com/watch?v=original';
      clipboard.copy.and.returnValue(false);
      fixture.detectChanges();
      fixture.componentInstance.detail.set({
        ...detailWithClips,
        sourceAssets: [{ type: 'video', originalInput: { type: 'youtube_url', url }, provenance: { provider: 'yt_dlp' } } as never],
      });
      fixture.detectChanges();

      (fixture.nativeElement.querySelector('[data-testid="page-header-subtitle-action"]') as HTMLButtonElement).click();

      expect(notify.showSuccess).not.toHaveBeenCalled();
      expect(notify.showTransientMessage).toHaveBeenCalledOnceWith('원본 URL을 복사하지 못했습니다.');
    });
  });

  it('상세를 못 불러오면 헤더 액션을 아예 그리지 않는다', () => {
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[data-testid="project-zip"]')).toBeNull();
    expect(fixture.nativeElement.querySelector('[data-testid="project-delete"]')).toBeNull();
  });

  it('헤더 아래에 메타 줄·입력 소스 줄을 두지 않는다 — 곧바로 작업 영역이다', () => {
    const component = fixture.componentInstance;
    fixture.detectChanges();
    component.error.set(null);
    component.detail.set({
      ...detailWithClips,
      sourceAssets: [{ provenance: { provider: 'yt_dlp', originalUrl: 'https://www.youtube.com/watch?v=x&list=y' } } as never],
    });
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('.detail-meta')).toBeNull();
    expect(el.querySelector('[data-testid="project-status"]')).toBeNull();
    expect(el.querySelector('.source-summary')).toBeNull();
    expect(el.textContent).not.toContain('yt-dlp');
    expect(el.textContent).not.toContain('입력 소스');
  });

  it('saves a manual dance member assignment, reloads detail, and never opens the confirm dialog', async () => {
    const component = fixture.componentInstance;
    component.detail.set(danceDetail);

    await component.assignDancePerson({
      sourcePersonId: 'person_1',
      memberKey: '허윤진',
      memberName: '허윤진',
    });

    // 배정은 지도에 줄 하나 적는 것이라 되돌릴 수 있다 — 확인 모달을 거치지 않는다(제거 확인).
    expect(confirmDialog.confirm).not.toHaveBeenCalled();
    expect(projects.assignDanceMember).toHaveBeenCalledOnceWith('project-dance', {
      sourcePersonId: 'person_1',
      memberKey: '허윤진',
      memberName: '허윤진',
    });
    expect(projects.getDetail).toHaveBeenCalledWith('project-dance');
    expect(component.detail()).toBe(danceDetail);
  });

  it('배정 성공 시 실행취소 동작이 붙은 스낵바를 띄운다', async () => {
    const component = fixture.componentInstance;
    component.detail.set(danceDetail);

    await component.assignDancePerson({
      sourcePersonId: 'person_1',
      memberKey: '허윤진',
      memberName: '허윤진',
    });

    expect(snackBar.open).toHaveBeenCalledOnceWith(
      'person_1의 클립을 허윤진로 합쳤습니다',
      '실행취소',
      jasmine.objectContaining({ duration: 6000 }),
    );
  });

  it('스낵바 실행취소 → 해제 API를 부르고 상세를 다시 불러온다', async () => {
    const component = fixture.componentInstance;
    component.detail.set(danceDetail);
    const undoAction = new Subject<void>();
    snackBar.open.and.returnValue({ onAction: () => undoAction.asObservable() });

    await component.assignDancePerson({
      sourcePersonId: 'person_1',
      memberKey: '허윤진',
      memberName: '허윤진',
    });
    projects.getDetail.calls.reset();
    undoAction.next();
    // undoDanceAssignment는 subscribe 콜백에서 void로 시작되는 fire-and-forget라 여기서
    // await할 promise가 없다 — 매크로태스크로 넘어가 모든 대기 중인 마이크로태스크를 비운다.
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(projects.deleteDanceMemberAssignment).toHaveBeenCalledOnceWith('project-dance', 'person_1');
    expect(projects.getDetail).toHaveBeenCalledOnceWith('project-dance');
  });

  it('실행취소는 해제 요청부터 재조회가 끝날 때까지 editing으로 잠그고, 끝나면 푼다', async () => {
    const component = fixture.componentInstance;
    component.detail.set(danceDetail);
    const undoAction = new Subject<void>();
    snackBar.open.and.returnValue({ onAction: () => undoAction.asObservable() });
    await component.assignDancePerson({ sourcePersonId: 'person_1', memberKey: '허윤진', memberName: '허윤진' });
    expect(component.editing()).toBeFalse();
    let finish!: () => void;
    projects.deleteDanceMemberAssignment.and.returnValue(new Promise<void>((resolve) => { finish = resolve; }));
    undoAction.next();
    expect(component.editing()).toBeTrue();
    finish();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(component.editing()).toBeFalse();
  });

  it('실행취소가 실패해도 잠금이 풀린다', async () => {
    const component = fixture.componentInstance;
    component.detail.set(danceDetail);
    const undoAction = new Subject<void>();
    snackBar.open.and.returnValue({ onAction: () => undoAction.asObservable() });
    projects.deleteDanceMemberAssignment.and.rejectWith(new Error('nope'));
    await component.assignDancePerson({ sourcePersonId: 'person_1', memberKey: '허윤진', memberName: '허윤진' });
    undoAction.next();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(component.editing()).toBeFalse();
  });

  it('실행취소가 실패하면(엔드포인트 없음 등) 기존 에러 토스트로 흘린다', async () => {
    const component = fixture.componentInstance;
    component.detail.set(danceDetail);
    const undoAction = new Subject<void>();
    snackBar.open.and.returnValue({ onAction: () => undoAction.asObservable() });
    projects.deleteDanceMemberAssignment.and.rejectWith(new Error('not found'));

    await component.assignDancePerson({
      sourcePersonId: 'person_1',
      memberKey: '허윤진',
      memberName: '허윤진',
    });
    undoAction.next();
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(notify.showToast).toHaveBeenCalled();
  });

  it('배정 실행취소도 다른 편집이 도는 중이면 버리지 않고, 그 편집이 끝난 뒤 해제를 보낸다', async () => {
    const component = fixture.componentInstance;
    component.detail.set(danceDetail);
    const undoAction = new Subject<void>();
    snackBar.open.and.returnValue({ onAction: () => undoAction.asObservable() });
    await component.assignDancePerson({ sourcePersonId: 'person_1', memberKey: '허윤진', memberName: '허윤진' });

    let finishTrim!: () => void;
    projects.trimDanceClip.and.returnValue(new Promise<void>((resolve) => { finishTrim = resolve; }));
    const trim = component.saveDanceRange({
      clip: { clipId: 'c1', title: 'clip 1', durationSec: 3 },
      range: { startSec: 0, endSec: 1 },
    });
    undoAction.next();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(projects.deleteDanceMemberAssignment).not.toHaveBeenCalled();
    expect(component.editing()).toBeTrue();

    finishTrim();
    await trim;
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(projects.deleteDanceMemberAssignment).toHaveBeenCalledOnceWith('project-dance', 'person_1');
    expect(component.editing()).toBeFalse();
  });

  describe('인물 칸 = persons 기준(T12 D3·D12)', () => {
    function danceWith(persons: ProjectPersonItem[], clipIds: string[] = persons.flatMap((p) => p.clipIds)): ProjectDetail {
      return {
        ...danceDetail,
        clips: clipIds.map((clipId) => ({
          clipId,
          title: clipId,
          durationSec: 2,
          personId: persons.find((p) => p.clipIds.includes(clipId))?.personId,
        })),
        persons,
        renders: [],
      };
    }
    const unknownRow = (clipIds: string[]): ProjectPersonItem =>
      ({ personId: 'unknown', personName: '미분류', unclassified: true, mappedMember: false, clipIds });

    it('확정 멤버가 있으면 클립 1개 익명도 보인다', () => {
      const component = fixture.componentInstance;
      component.detail.set(danceWith([
        { personId: 'person_5', personName: 'person 5', mappedMember: false, clipIds: ['c1'] },
        { personId: '카즈하', personName: '카즈하', mappedMember: true, clipIds: [] },
      ]));

      expect(component.visiblePersons().map((p) => p.personId)).toEqual(['카즈하', 'person_5']);
    });

    it('확정 멤버가 없으면 클립 1개 익명은 숨고, 2개 이상만 보인다', () => {
      const component = fixture.componentInstance;
      component.detail.set(danceWith([
        { personId: 'person_1', personName: 'person 1', mappedMember: false, clipIds: ['c1'] },
        { personId: 'person_2', personName: 'person 2', mappedMember: false, clipIds: ['c2', 'c3'] },
      ]));

      expect(component.visiblePersons().map((p) => p.personId)).toEqual(['person_2']);
    });

    it('클립 0개 익명은 숨고, 클립 0개 확정 멤버는 보인다', () => {
      const component = fixture.componentInstance;
      component.detail.set(danceWith([
        { personId: 'person_1', personName: 'person 1', mappedMember: false, clipIds: [] },
        { personId: 'sakura', personName: '사쿠라', mappedMember: true, clipIds: [] },
      ]));

      expect(component.visiblePersons().map((p) => p.personId)).toEqual(['sakura']);
    });

    it('미분류와 함께 등장 대기는 숨기고 확정 멤버와 익명 인물만 표시한다', () => {
      const component = fixture.componentInstance;
      component.detail.set(danceWith([
        unknownRow(['c9']),
        { personId: 'shared', sharedReview: true, clipIds: ['group_1'] },
        { personId: 'person_2', personName: 'person 2', mappedMember: false, clipIds: ['c2', 'c3'] },
        { personId: 'sakura', personName: '사쿠라', mappedMember: true, clipIds: ['c1'] },
      ]));

      expect(component.visiblePersons().map((p) => p.personId)).toEqual(['sakura', 'person_2']);
    });

    it('클립 0개 미분류는 숨는다(방어 — 백엔드가 원래 빼 준다)', () => {
      const component = fixture.componentInstance;
      component.detail.set(danceWith([
        { personId: 'sakura', personName: '사쿠라', mappedMember: true, clipIds: ['c1'] },
        unknownRow([]),
      ]));

      expect(component.visiblePersons().map((p) => p.personId)).toEqual(['sakura']);
    });

    it('안무는 renders를 읽지 않는다 — renders가 있어도 인물 칸은 persons만', () => {
      const component = fixture.componentInstance;
      component.detail.set({
        ...danceWith([{ personId: 'sakura', personName: '사쿠라', mappedMember: true, clipIds: ['c1'] }]),
        renders: [{ renderId: 'ghost', personId: 'ghost', title: 'ghost', durationSec: 1, mappedMember: true }],
      });

      expect(component.visiblePersons().map((p) => p.personId)).toEqual(['sakura']);
    });

    it('기본 선택 = 클립 있는 첫 확정 멤버', async () => {
      const component = fixture.componentInstance;
      projects.getDetail.and.resolveTo(danceWith([
        { personId: 'person_2', personName: 'person 2', mappedMember: false, clipIds: ['c2', 'c3'] },
        { personId: '허윤진', personName: '허윤진', mappedMember: true, clipIds: [] },
        { personId: 'sakura', personName: '사쿠라', mappedMember: true, clipIds: ['c1'] },
      ]));

      // 라우트 목에 projectId가 없어 ngOnInit은 로드하지 않는다 — 로드 경로를 직접 태운다.
      await component['load']('project-dance');

      expect(component.selectedPersonId()).toBe('sakura');
      expect(component.selectedPerson()?.personId).toBe('sakura');
    });

    it('숨긴 미분류에 클립이 있어도 기본 선택은 표시된 멤버다', async () => {
      const component = fixture.componentInstance;
      projects.getDetail.and.resolveTo(danceWith([
        { personId: '허윤진', personName: '허윤진', mappedMember: true, clipIds: [] },
        unknownRow(['c9']),
      ]));

      // 라우트 목에 projectId가 없어 ngOnInit은 로드하지 않는다 — 로드 경로를 직접 태운다.
      await component['load']('project-dance');

      expect(component.selectedPersonId()).toBe('허윤진');
    });

    it('보이는 행이 전부 클립 0개(확정 멤버뿐)여도 기본 선택 = 첫 행 — 선택을 비워 두지 않는다', async () => {
      const component = fixture.componentInstance;
      projects.getDetail.and.resolveTo(danceWith([
        { personId: '허윤진', personName: '허윤진', mappedMember: true, clipIds: [] },
        { personId: 'sakura', personName: '사쿠라', mappedMember: true, clipIds: [] },
      ]));

      await component['load']('project-dance');

      expect(component.selectedPersonId()).toBe('허윤진');
    });

    it('selectedPersonClips = 선택 인물의 clipIds로 거른 클립', () => {
      const component = fixture.componentInstance;
      const detail = danceWith([
        { personId: 'sakura', personName: '사쿠라', mappedMember: true, clipIds: ['c1', 'c3'] },
        unknownRow(['c2']),
      ]);
      component.detail.set(detail);

      component.selectPerson(detail.persons[1]);
      expect(component.selectedPersonClips()).toEqual([]);

      component.selectPerson(detail.persons[0]);
      expect(component.selectedPersonClips().map((c) => c.clipId)).toEqual(['c1', 'c3']);
    });

    it('인물을 고르지 않았으면 selectedPersonClips는 비어 있다 — 전 클립이 생성 대상처럼 보이면 안 된다', () => {
      const component = fixture.componentInstance;
      component.detail.set(danceWith([
        { personId: 'sakura', personName: '사쿠라', mappedMember: true, clipIds: ['c1'] },
        unknownRow(['c2']),
      ]));
      component.selectedPersonId.set(null);

      expect(component.selectedPersonClips()).toEqual([]);
    });

    it('조용한 새로고침 뒤에도 고른 인물이 아직 보이면 그대로 둔다(기본 인물로 튀지 않는다)', async () => {
      const component = fixture.componentInstance;
      const detail = danceWith([
        { personId: 'sakura', personName: '사쿠라', mappedMember: true, clipIds: ['c1'] },
        { personId: 'person_2', personName: 'person 2', mappedMember: false, clipIds: ['c2', 'c3'] },
      ]);
      projects.getDetail.and.resolveTo(detail);
      await component['load']('project-dance');
      expect(component.selectedPersonId()).toBe('sakura');

      component.selectPerson(detail.persons[1]);
      await component['load']('project-dance');

      expect(component.selectedPersonId()).toBe('person_2');
    });

    it('고른 인물이 새로고침 뒤 사라지면(미분류를 비움) 기본 인물로 돌아간다 — 선택이 비지 않는다', async () => {
      const component = fixture.componentInstance;
      const before = danceWith([
        { personId: 'sakura', personName: '사쿠라', mappedMember: true, clipIds: ['c1'] },
        unknownRow(['c2']),
      ]);
      component.detail.set(before);
      component.selectPerson(before.persons[1]);
      component.selectClip(before.clips.find(clip => clip.clipId === 'c2')!);
      projects.getDetail.and.resolveTo(danceWith([
        { personId: 'sakura', personName: '사쿠라', mappedMember: true, clipIds: ['c1', 'c2'] },
        unknownRow([]),
      ]));

      await component.moveDanceClips({ clipIds: ['c2'], sourcePersonId: 'unknown', targetPersonId: 'sakura' });

      expect(component.visiblePersons().map((p) => p.personId)).toEqual(['sakura']);
      expect(component.selectedPersonId()).toBe('sakura');
      expect(component.selectedPerson()?.personId).toBe('sakura');
    });
  });

  it('does not present archived storyboard renders as a completed-video result', () => {
    const component = fixture.componentInstance;
    component.detail.set(legacyStoryboardDetail);

    fixture.detectChanges();

    expect(component.visiblePersons()).toEqual([]);
    expect(component.selectedPerson()).toBeNull();
    expect(fixture.nativeElement.querySelector('app-shortform-director-result-detail')).toBeNull();
    expect(fixture.nativeElement.querySelector('video')).toBeNull();
    expect(fixture.nativeElement.textContent).not.toContain('최종 영상');
  });

  it('shows people with even one visible scene while keeping unknown and fully hidden people out', () => {
    const component = fixture.componentInstance;
    const detail: ProjectDetail = {
      ...danceDetail, category: 'person', pluginName: 'person_highlight',
      clips: [
        { clipId: 'a', title: 'a', durationSec: 1 },
        { clipId: 'b', title: 'b', durationSec: 1 },
        { clipId: 'c', title: 'c', durationSec: 1 },
        { clipId: 'd', title: 'd', durationSec: 1 },
        { clipId: 'e', title: 'e', durationSec: 1, excluded: true },
      ],
      persons: [
        { personId: 'unidentified', personName: '인물 확인 필요', clipIds: ['a', 'b', 'c'], unclassified: true },
        { personId: 'few', personName: 'few', clipIds: ['a', 'b'] },
        { personId: 'enough', personName: 'enough', clipIds: ['a', 'b', 'c', 'e'] },
        { personId: 'hidden-third', personName: 'hidden-third', clipIds: ['c', 'd', 'e'] },
        { personId: 'one', personName: 'one', clipIds: ['d'] },
        { personId: 'hidden-only', personName: 'hidden-only', clipIds: ['e'] },
      ],
    };
    component.detail.set(detail);
    component.selectedPersonId.set('few');

    expect(component.visiblePersons().map((person) => person.personId)).toEqual(['enough', 'few', 'hidden-third', 'one']);
    (component as any).selectDefaultMedia(detail);
    expect(component.selectedPersonId()).toBe('few');
    expect(component.selectedPersonClips().map((clip) => clip.clipId)).toEqual(['a', 'b']);
  });

  it('인물 결과 첫 진입은 제외된 장면을 뺀 장면 수가 가장 많은 맨 위 카드를 선택한다', async () => {
    routeParams['projectId'] = 'person-project';
    projects.getDetail.and.resolveTo({ ...danceDetail, projectId: 'person-project', category: 'person',
      pluginName: 'person_highlight',
      clips: [
        { clipId: 'a', title: 'a', durationSec: 1 },
        { clipId: 'b', title: 'b', durationSec: 1 },
        { clipId: 'c', title: 'c', durationSec: 1, excluded: true },
      ],
      persons: [
        { personId: 'person_1', clipIds: ['a', 'c', 'missing'] },
        { personId: 'person_10', clipIds: ['a', 'b'] },
      ],
    });
    const component = fixture.componentInstance;
    await component.ngOnInit();
    fixture.detectChanges();
    expect(component.selectedPersonId()).toBe('person_10');
    const cards = fixture.nativeElement.querySelectorAll('.person-shell');
    expect(cards[0].classList.contains('selected')).toBeTrue();
    expect(cards[0].textContent).toContain('인물 10');
  });

  it('zipCount: videoPath 없는 클립은 세지 않는다', () => {
    const component = fixture.componentInstance;
    component.detail.set(detailWithClips);

    expect(component.zipCount()).toBe(2);
  });

  it('counts person scenes without MP4 files and downloads the selected range on demand', async () => {
    const component = fixture.componentInstance;
    const scene = {
      clipId: 'scene-1', title: '장면 1', durationSec: 2,
      sourceStartSec: 3, sourceEndSec: 5, personIds: ['person_1'],
    };
    component.detail.set({ ...danceDetail, projectId: 'person-project', category: 'person', clips: [scene] });
    projects.projectPersonClipUrl.and.returnValue('http://x/v1/projects/person-project/person/clips/scene-1/download');

    expect(component.zipCount()).toBe(1);
    await component.downloadPersonClip(scene);

    expect(projects.projectPersonClipUrl).toHaveBeenCalledWith('person-project', 'scene-1');
    expect(download.save).toHaveBeenCalledWith(
      'http://x/v1/projects/person-project/person/clips/scene-1/download', '장면 1.mp4',
    );
  });

  it('ZIP 버튼: 다운로드할 클립이 없으면 비활성화된다', () => {
    const component = fixture.componentInstance;
    // 첫 detectChanges가 ngOnInit을 태운다(paramMap에 projectId가 없어 error가 채워짐) —
    // 상세 패널을 렌더하려면 error를 비우고 detail을 채운 뒤 다시 그려야 한다.
    fixture.detectChanges();
    component.error.set(null);
    component.detail.set({ ...danceDetail, clips: [] });
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector(
      '[data-testid="project-zip"]',
    ) as HTMLButtonElement;
    expect(button.disabled).toBeTrue();
  });

  it('전체 ZIP 버튼: 클릭하면 zip URL로 저장하고 진행 중 비활성', async () => {
    const component = fixture.componentInstance;
    component.detail.set(detailWithClips);
    projects.projectZipUrl.and.returnValue('http://x/v1/projects/p1/zip');

    const promise = component.downloadAllZip();
    expect(component.zipping()).toBeTrue();
    await promise;

    expect(download.save).toHaveBeenCalled();
    expect(component.zipping()).toBeFalse();
  });

  it('선택 장면 ZIP은 선택 토큰을 만든 뒤 해당 장면 수만 저장한다', async () => {
    const component = fixture.componentInstance;
    component.detail.set({ ...danceDetail, projectId: 'project-person', category: 'person',
      pluginName: 'person_highlight' });
    await component.downloadSelectedPersonZip({ personId: 'p1', clipIds: ['c1', 'c2'] });
    expect(projects.selectedPersonZipUrl).toHaveBeenCalledOnceWith('project-person', 'p1', ['c1', 'c2']);
    expect(download.save.calls.mostRecent().args[0]).toBe('http://x/selected.zip');
    expect(snackBar.open.calls.mostRecent().args[0]).toBe('2개 클립을 저장했습니다');
  });

  it('전체 ZIP: 이미 진행 중이면 중복 호출을 막는다', async () => {
    const component = fixture.componentInstance;
    component.detail.set(detailWithClips);
    projects.projectZipUrl.and.returnValue('http://x/v1/projects/p1/zip');
    let resolveSave!: (value: { status: string }) => void;
    download.save.and.returnValue(
      new Promise((resolve) => {
        resolveSave = resolve;
      }),
    );

    const first = component.downloadAllZip();
    const second = component.downloadAllZip();
    resolveSave({ status: 'completed' });
    await Promise.all([first, second]);

    expect(download.save).toHaveBeenCalledTimes(1);
  });

  it('전체 ZIP: 취소되면 성공 스낵바를 띄우지 않는다', async () => {
    const component = fixture.componentInstance;
    component.detail.set(detailWithClips);
    projects.projectZipUrl.and.returnValue('http://x/v1/projects/p1/zip');
    download.save.and.resolveTo({ status: 'cancelled' });

    await component.downloadAllZip();

    expect(snackBar.open).not.toHaveBeenCalled();
    expect(notify.showToast).not.toHaveBeenCalled();
  });

  it('전체 ZIP: 인물을 지정하면 그 인물의 클립 수만 스낵바에 담는다', async () => {
    const component = fixture.componentInstance;
    component.detail.set(detailWithClips);
    projects.projectZipUrl.and.returnValue('http://x/v1/projects/p1/zip');
    download.save.and.resolveTo({ status: 'completed' });

    await component.downloadAllZip('person_1');

    expect(snackBar.open).toHaveBeenCalledWith('1개 클립을 저장했습니다', '닫기', { duration: 4000 });
  });

  it('전체 ZIP: 저장 완료 시 전체 클립 수를 스낵바에 담는다', async () => {
    const component = fixture.componentInstance;
    component.detail.set(detailWithClips);
    projects.projectZipUrl.and.returnValue('http://x/v1/projects/p1/zip');
    download.save.and.resolveTo({ status: 'completed' });

    await component.downloadAllZip();

    expect(snackBar.open).toHaveBeenCalledWith('2개 클립을 저장했습니다', '닫기', { duration: 4000 });
  });

  it('전체 ZIP: 저장 실패 시 토스트를 띄우고 zipping을 해제한다', async () => {
    const component = fixture.componentInstance;
    component.detail.set(detailWithClips);
    projects.projectZipUrl.and.returnValue('http://x/v1/projects/p1/zip');
    download.save.and.rejectWith(new Error('boom'));

    await component.downloadAllZip();

    expect(notify.showToast).toHaveBeenCalled();
    expect(component.zipping()).toBeFalse();
  });

  it('전체 ZIP: 저장이 중단되면(interrupted) 실패 토스트를 띄운다(C2)', async () => {
    const component = fixture.componentInstance;
    component.detail.set(detailWithClips);
    projects.projectZipUrl.and.returnValue('http://x/v1/projects/p1/zip');
    download.save.and.resolveTo({ status: 'interrupted' });

    await component.downloadAllZip();

    expect(snackBar.open).not.toHaveBeenCalled();
    expect(notify.showToast).toHaveBeenCalledOnceWith(
      jasmine.objectContaining({ category: 'internal' }),
    );
  });

  // ── 아이콘·스피너와 라벨 사이 간격 (T7 F1과 같은 결함, 2026-09-03 T8) ────────────
  // Material은 버튼의 아이콘 간격을 `> .mat-icon`에만 준다 — 아이콘 자리에 낀
  // mat-progress-spinner는 그 선택자에 안 걸려 간격 0으로 라벨에 딱 붙고, 폭도 다르면
  // ZIP을 누를 때마다 라벨이 옆으로 움찔한다. 두 상태를 같은 자로 재서 못 박는다.
  describe('전체 ZIP 버튼: 아이콘 칸과 라벨 사이(.zip-btn)', () => {
    /** 아이콘 칸이 가로로 **차지하는 자리** — margin까지 세야 라벨이 어디서 시작하는지가 나온다. */
    function footprint(el: HTMLElement): number {
      const cs = getComputedStyle(el);
      return parseFloat(cs.marginLeft) + el.getBoundingClientRect().width + parseFloat(cs.marginRight);
    }

    /** 아이콘일 때 / 스피너일 때의 (간격, 차지하는 폭)을 한 번에 잰다. */
    async function measureBothStates(): Promise<{
      icon: { gap: number; footprint: number };
      spinner: { gap: number; footprint: number };
    }> {
      const component = fixture.componentInstance;
      // 첫 detectChanges가 ngOnInit을 태운다(paramMap에 projectId가 없어 error가 채워짐) —
      // 상세 패널을 렌더하려면 error를 비우고 detail을 채운 뒤 다시 그려야 한다.
      fixture.detectChanges();
      component.error.set(null);
      component.detail.set(detailWithClips);
      projects.projectZipUrl.and.returnValue('http://x/v1/projects/p1/zip');
      fixture.detectChanges();

      const btn = fixture.nativeElement.querySelector('[data-testid="project-zip"]') as HTMLElement;
      const label = fixture.nativeElement.querySelector(
        '[data-testid="project-zip-label"]',
      ) as HTMLElement;
      const gapTo = (slotEl: HTMLElement): number =>
        label.getBoundingClientRect().left - slotEl.getBoundingClientRect().right;

      const iconEl = btn.querySelector('mat-icon') as HTMLElement;
      const icon = { gap: gapTo(iconEl), footprint: footprint(iconEl) };

      // 가짜 저장은 즉시 끝나 "준비 중"이 없다 — 붙잡아 스피너가 떠 있는 창을 연다
      // (바로 위 '중복 호출을 막는다' 테스트가 쓰는 것과 같은 수법).
      let resolveSave!: (value: { status: string }) => void;
      download.save.and.returnValue(
        new Promise((resolve) => {
          resolveSave = resolve;
        }),
      );
      const pending = component.downloadAllZip();
      fixture.detectChanges();

      const spinEl = btn.querySelector('mat-progress-spinner') as HTMLElement;
      const spinner = { gap: gapTo(spinEl), footprint: footprint(spinEl) };

      resolveSave({ status: 'completed' });
      await pending;
      return { icon, spinner };
    }

    it('아이콘도 스피너도 라벨에 붙어 있지 않고, 간격이 서로 같다', async () => {
      const { icon, spinner } = await measureBothStates();

      expect(icon.gap).withContext('아이콘이 글자에 딱 붙었다').toBeGreaterThan(4);
      expect(spinner.gap)
        .withContext('스피너가 글자에 딱 붙었다 — Material의 아이콘 간격이 스피너엔 안 걸린다')
        .toBeCloseTo(icon.gap, 1);
    });

    it('스피너가 아이콘과 똑같은 자리를 차지한다 — 누를 때마다 라벨이 움찔하지 않게', async () => {
      const { icon, spinner } = await measureBothStates();

      // 폭(diameter)과 앞쪽 offset(margin-left) 중 하나만 어긋나도 라벨 시작점이 달라진다.
      expect(spinner.footprint)
        .withContext('스피너가 뜰 때 아이콘 칸의 폭이 달라진다 — 라벨이 옆으로 튄다')
        .toBeCloseTo(icon.footprint, 1);
    });
  });

  it('downloadFile: 저장 완료 시 스낵바를 띄운다', async () => {
    const component = fixture.componentInstance;
    download.save.and.resolveTo({ status: 'completed' });

    await component.downloadFile('http://x/v1/projects/p1/file?path=a.mp4&mediaToken=t', '클립 제목');

    const [url, filename] = download.save.calls.mostRecent().args;
    expect(url).toBe('http://x/v1/projects/p1/file?path=a.mp4&mediaToken=t');
    expect(filename.endsWith('.mp4')).toBeTrue();
    expect(snackBar.open).toHaveBeenCalledWith('저장했습니다', '닫기', { duration: 4000 });
  });

  it('downloadFile: 취소되면 스낵바를 띄우지 않는다', async () => {
    const component = fixture.componentInstance;
    download.save.and.resolveTo({ status: 'cancelled' });

    await component.downloadFile('http://x/v1/projects/p1/file?path=a.mp4&mediaToken=t', '클립 제목');

    expect(snackBar.open).not.toHaveBeenCalled();
  });

  it('downloadFile: 저장이 중단되면(interrupted) 실패 토스트를 띄운다(C2)', async () => {
    const component = fixture.componentInstance;
    download.save.and.resolveTo({ status: 'interrupted' });

    await component.downloadFile('http://x/v1/projects/p1/file?path=a.mp4&mediaToken=t', '클립 제목');

    expect(snackBar.open).not.toHaveBeenCalled();
    expect(notify.showToast).toHaveBeenCalledOnceWith(
      jasmine.objectContaining({ category: 'internal' }),
    );
  });

  it('삭제: 확인 후 보관함으로 복귀한다', async () => {
    const component = fixture.componentInstance;
    component.detail.set(danceDetail);
    confirmDialog.confirm.and.resolveTo(true);

    await component.confirmDelete();

    expect(jobs.deleteArchiveEntry).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/projects']);
  });

  it('삭제 실패: 토스트를 띄우고 페이지에 머문다', async () => {
    const component = fixture.componentInstance;
    component.detail.set(danceDetail);
    confirmDialog.confirm.and.resolveTo(true);
    jobs.deleteArchiveEntry.and.rejectWith(new Error('boom'));

    await component.confirmDelete();

    expect(notify.showToast).toHaveBeenCalled();
    expect(router.navigate).not.toHaveBeenCalled();
  });

  it('삭제: 확인을 취소하면 아무 것도 하지 않는다', async () => {
    const component = fixture.componentInstance;
    component.detail.set(danceDetail);
    confirmDialog.confirm.and.resolveTo(false);

    await component.confirmDelete();

    expect(jobs.deleteArchiveEntry).not.toHaveBeenCalled();
    expect(router.navigate).not.toHaveBeenCalled();
  });

  it('삭제: 확인 다이얼로그에 클립 개수와 삭제 문구를 담아 호출한다', async () => {
    const component = fixture.componentInstance;
    component.detail.set(detailWithClips);
    confirmDialog.confirm.and.resolveTo(true);

    await component.confirmDelete();

    expect(confirmDialog.confirm).toHaveBeenCalledWith({
      title: '이 프로젝트를 삭제할까요?',
      message: `「${detailWithClips.title}」의 클립 2개와 결과 영상이 디스크에서 함께 삭제됩니다. 되돌릴 수 없습니다.`,
      confirmLabel: '삭제',
      danger: true,
    });
  });

  describe('클립 삭제·이동 — 서버에 저장(T12 §4.2)', () => {
    const clipDetail: ProjectDetail = {
      ...danceDetail,
      clips: [
        { clipId: 'c1', title: '클립 1', durationSec: 2, personId: 'person_1' },
        { clipId: 'c2', title: '클립 2', durationSec: 2, personId: 'person_1' },
      ],
      persons: [
        { personId: 'person_1', personName: 'person 1', mappedMember: false, clipIds: ['c1', 'c2'] },
        { personId: 'sakura', personName: '사쿠라', mappedMember: true, clipIds: [] },
        { personId: 'unknown', personName: '미분류', mappedMember: false, unclassified: true, clipIds: [] },
      ],
    };
    const reloaded: ProjectDetail = { ...clipDetail, title: 'reloaded' };

    /** 스낵바 되돌리기는 subscribe 콜백에서 void로 시작된다 — 매크로태스크로 넘겨 마이크로태스크를 비운다. */
    const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

    beforeEach(() => {
      projects.getDetail.and.resolveTo(reloaded);
    });

    it('hideDanceClip: 숨김 API → 로딩 화면 없이 새로고침 → 되돌리기 스낵바', async () => {
      const component = fixture.componentInstance;
      component.detail.set(clipDetail);
      let loadingDuringReload: boolean | undefined;
      projects.getDetail.and.callFake(async () => {
        loadingDuringReload = component.loading();
        return reloaded;
      });

      await component.hideDanceClip('c1');

      expect(projects.hideDanceClip).toHaveBeenCalledOnceWith('project-dance', 'c1');
      expect(projects.getDetail).toHaveBeenCalledOnceWith('project-dance');
      expect(loadingDuringReload).toBeFalse();
      expect(component.detail()).toBe(reloaded);
      expect(snackBar.open).toHaveBeenCalledOnceWith(
        '클립을 삭제했습니다',
        '되돌리기',
        jasmine.objectContaining({ duration: 6000 }),
      );
    });

    it('hideDanceClip 되돌리기 → 복원 API → 새로고침', async () => {
      const component = fixture.componentInstance;
      component.detail.set(clipDetail);
      const undoAction = new Subject<void>();
      snackBar.open.and.returnValue({ onAction: () => undoAction.asObservable() });

      await component.hideDanceClip('c1');
      projects.getDetail.calls.reset();
      undoAction.next();
      await flush();

      expect(projects.restoreDanceClip).toHaveBeenCalledOnceWith('project-dance', 'c1');
      expect(projects.getDetail).toHaveBeenCalledOnceWith('project-dance');
    });

    it('hideDanceClip 되돌리기 시점에 다른 프로젝트를 보고 있으면 복원만 하고 그 화면은 다시 불러오지 않는다', async () => {
      const component = fixture.componentInstance;
      component.detail.set(clipDetail);
      const undoAction = new Subject<void>();
      snackBar.open.and.returnValue({ onAction: () => undoAction.asObservable() });

      await component.hideDanceClip('c1');
      const otherProject: ProjectDetail = { ...danceDetail, projectId: 'other-project' };
      component.detail.set(otherProject);
      projects.getDetail.calls.reset();
      undoAction.next();
      await flush();

      expect(projects.restoreDanceClip).toHaveBeenCalledOnceWith('project-dance', 'c1');
      expect(projects.getDetail).not.toHaveBeenCalled();
      expect(component.detail()).toBe(otherProject);
    });

    it('hideDanceClip 실패 → 에러 토스트, 스낵바·새로고침 없음', async () => {
      const component = fixture.componentInstance;
      component.detail.set(clipDetail);
      const err = new Error('boom');
      projects.hideDanceClip.and.rejectWith(err);

      await component.hideDanceClip('c1');

      expect(notify.showToast).toHaveBeenCalledOnceWith(appErrorFrom(err));
      expect(snackBar.open).not.toHaveBeenCalled();
      expect(projects.getDetail).not.toHaveBeenCalled();
      expect(component.detail()).toBe(clipDetail);
    });

    it('hideDanceClip 되돌리기 실패 → 에러 토스트', async () => {
      const component = fixture.componentInstance;
      component.detail.set(clipDetail);
      const undoAction = new Subject<void>();
      snackBar.open.and.returnValue({ onAction: () => undoAction.asObservable() });
      const err = new Error('restore failed');
      projects.restoreDanceClip.and.rejectWith(err);

      await component.hideDanceClip('c1');
      undoAction.next();
      await flush();

      expect(notify.showToast).toHaveBeenCalledOnceWith(appErrorFrom(err));
    });

    it('되돌리기(복원)도 요청부터 재조회가 끝날 때까지 editing으로 잠근다', async () => {
      const component = fixture.componentInstance;
      component.detail.set(clipDetail);
      const undo = new Subject<void>();
      snackBar.open.and.returnValue({ onAction: () => undo.asObservable() });
      await component.hideDanceClip('c1');
      let finish!: () => void;
      projects.restoreDanceClip.and.returnValue(new Promise<void>((resolve) => { finish = resolve; }));
      undo.next();
      expect(component.editing()).toBeTrue();
      finish();
      await flush();
      expect(component.editing()).toBeFalse();
    });

    describe('다른 편집이 도는 중에 누른 되돌리기 — 버리지 않는다(스낵바는 이미 사라졌다)', () => {
      /** hideDanceClip 한 번 → 되돌리기 Subject. 그 뒤 일괄 이동을 걸어 두고(대기) 되돌리기를 누른다. */
      async function hideThenStartMove(component: ProjectsDetailPageComponent) {
        component.detail.set(clipDetail);
        const undo = new Subject<void>();
        snackBar.open.and.returnValue({ onAction: () => undo.asObservable() });
        await component.hideDanceClip('c1');

        const order: string[] = [];
        let settleMove!: (ok: boolean) => void;
        projects.applyDanceClipAction.and.callFake(() => new Promise<void>((resolve, reject) => {
          order.push('move:start');
          settleMove = (ok) => {
            order.push('move:end');
            if (ok) resolve(); else reject(new Error('move failed'));
          };
        }));
        let finishRestore!: () => void;
        projects.restoreDanceClip.and.callFake(() => new Promise<void>((resolve) => {
          order.push('restore:start');
          finishRestore = resolve;
        }));
        const move = component.moveDanceClips({ clipIds: ['c2'], sourcePersonId: 'person_1', targetPersonId: 'sakura' });
        await flush();
        expect(order).toEqual(['move:start']);
        return { undo, order, move, settleMove: (ok: boolean) => settleMove(ok), finishRestore: () => finishRestore() };
      }

      it('앞 편집이 끝난 뒤 이어서 보낸다(순서대로), 잠금은 둘 다 끝날 때까지 켜져 있다', async () => {
        const component = fixture.componentInstance;
        const { undo, order, move, settleMove, finishRestore } = await hideThenStartMove(component);

        undo.next();
        await flush();
        expect(projects.restoreDanceClip).withContext('앞 편집이 도는 동안엔 아직 안 보낸다').not.toHaveBeenCalled();
        expect(component.editing()).toBeTrue();

        // 실행취소가 줄에 서 있는 동안 새 편집 클릭은 연타 가드로 무시한다.
        await component.hideDanceClips(['c2']);
        expect(projects.applyDanceClipAction).toHaveBeenCalledTimes(1);

        settleMove(true);
        await move;
        await flush();
        expect(projects.restoreDanceClip).toHaveBeenCalledOnceWith('project-dance', 'c1');
        expect(order).toEqual(['move:start', 'move:end', 'restore:start']);
        expect(component.editing()).withContext('되돌리기가 아직 도는 중').toBeTrue();

        finishRestore();
        await flush();
        expect(component.editing()).toBeFalse();
      });

      it('앞 편집이 실패해도 되돌리기는 막히지 않고 돈다', async () => {
        const component = fixture.componentInstance;
        const { undo, order, move, settleMove, finishRestore } = await hideThenStartMove(component);

        undo.next();
        await flush();
        settleMove(false);
        await move;
        await flush();
        expect(notify.showToast).withContext('앞 편집 실패는 그대로 알린다').toHaveBeenCalledTimes(1);
        expect(projects.restoreDanceClip).toHaveBeenCalledOnceWith('project-dance', 'c1');
        expect(order).toEqual(['move:start', 'move:end', 'restore:start']);
        expect(component.editing()).toBeTrue();

        finishRestore();
        await flush();
        expect(component.editing()).toBeFalse();
      });
    });

    it('일괄 이동 실패는 토스트로 알리고 기존 결과를 유지한다', async () => {
      const component = fixture.componentInstance;
      component.detail.set(clipDetail);
      const error = new Error('move failed');
      projects.applyDanceClipAction.and.rejectWith(error);
      await component.moveDanceClips({ clipIds: ['c1', 'c2'], sourcePersonId: 'person_1', targetPersonId: 'sakura' });
      expect(notify.showToast).toHaveBeenCalledOnceWith(appErrorFrom(error));
      expect(component.detail()).toBe(clipDetail);
      expect(component.editing()).toBeFalse();
      expect(projects.getDetail).not.toHaveBeenCalled();
    });
  });

  describe('상태 안내 패널 (app-state-panel)', () => {
    /** ngOnInit의 최초 로드가 끝난 뒤에 상태를 세운다 — 먼저 세우면 로드가 덮어쓴다. */
    async function render(apply: () => void): Promise<HTMLElement> {
      fixture.detectChanges();
      await fixture.whenStable();
      apply();
      fixture.detectChanges();
      await fixture.whenStable();
      fixture.detectChanges();
      return fixture.nativeElement as HTMLElement;
    }

    // 로딩은 상태 패널(카드)이 아니라 공용 페이지 로더다 — 다른 화면의 "불러오는 중"과 같은
    // 자리·크기(2026-10-15 페이지 로더 통일).
    it('로딩 중이면 공용 페이지 로더를 문구 그대로 보여준다', async () => {
      const host = await render(() => fixture.componentInstance.loading.set(true));
      expect(host.querySelector('app-state-panel')).toBeNull();
      const loader = host.querySelector('app-page-loading')!;
      expect(loader).toBeTruthy();
      expect(loader.textContent).toContain('프로젝트 결과를 불러오는 중…');
    });

    it('에러면 error 패널에 원문을 message로 싣는다', async () => {
      const host = await render(() => {
        fixture.componentInstance.loading.set(false);
        fixture.componentInstance.error.set('앱 내부 서버에 연결하지 못했습니다.');
      });
      const panel = host.querySelector('app-state-panel')!;
      expect(panel.querySelector('.sp-panel.sp-error')).toBeTruthy();
      expect(panel.querySelector('.sp-heading')!.textContent!.trim()).toBe('결과를 불러오지 못했어요');
      expect(panel.querySelector('.sp-message')!.textContent!.trim())
        .toBe('앱 내부 서버에 연결하지 못했습니다.');
    });

    // 호스트가 `height: 100vh` flex 컬럼이라, 중앙 정렬 규칙이 없으면 패널이 거의 전체 높이의
    // 빈 공간 맨 위에 붙는다. 중앙 정렬은 공유 부품이 아니라 이 화면(호출부)의 책임이다.
    it('상태 패널을 화면 한복판에 놓는다 (배치는 호출부 책임)', async () => {
      const host = await render(() => {
        fixture.componentInstance.loading.set(false);
        fixture.componentInstance.error.set('앱 내부 서버에 연결하지 못했습니다.');
      });
      const style = getComputedStyle(host.querySelector('app-state-panel')!);
      expect(style.display).toBe('grid');
      expect(style.alignItems).toBe('center');
      expect(style.justifyItems).toBe('center');
    });

    it('결과가 없으면 empty 패널을 문구 그대로 보여준다', async () => {
      const host = await render(() => {
        fixture.componentInstance.loading.set(false);
        fixture.componentInstance.error.set(null);
        fixture.componentInstance.detail.set(null);
      });
      const panel = host.querySelector('app-state-panel')!;
      expect(panel.querySelector('.sp-panel.sp-empty')).toBeTruthy();
      expect(panel.textContent).toContain('프로젝트 결과가 없습니다.');
    });
  });

  describe('클립 구간 자르기', () => {
    const dialogDetail: ProjectDetail = {
      ...danceDetail,
      projectId: 'project-dialog',
      category: 'dialog',
      clips: [{ clipId: '1', title: 'clip', durationSec: 39, videoPath: '/tmp/c1.mp4' }],
    };

    it('저장 중엔 그 클립을 잠그고, 끝나면 상세를 다시 불러온다', async () => {
      const component = fixture.componentInstance;
      component.detail.set(dialogDetail);
      projects.getDetail.and.resolveTo(dialogDetail);
      projects.trimClip.and.callFake(async () => {
        // 저장이 진행되는 동안엔 잠겨 있어야 한다 — 중복 저장이 막히는 근거다
        expect(component.trimmingClipId()).toBe('1');
      });

      await component.onTrimSave({ clip: dialogDetail.clips[0], range: { startSec: 5, endSec: 32 } });

      expect(projects.trimClip).toHaveBeenCalledWith('project-dialog', '1', { startSec: 5, endSec: 32 });
      // 응답 클립만 끼워넣으면 새 경로의 mediaToken이 없어 재생이 깨진다 → 상세를 통째로 다시 받는다
      expect(projects.getDetail).toHaveBeenCalled();
      expect(component.trimmingClipId()).toBeNull();
      expect(snackBar.open).toHaveBeenCalled();
    });

    it('저장 뒤 새로고침은 로딩 화면 없이 끝난다 — 결과 화면을 다시 만들지 않는다', async () => {
      const component = fixture.componentInstance;
      const clip = { ...dialogDetail.clips[0], originalDurationSec: 39 };
      const detail = { ...dialogDetail, clips: [clip] };
      fixture.detectChanges();
      component.error.set(null);
      component.detail.set(detail);
      fixture.detectChanges();

      // 새로고침 전의 결과 컴포넌트 — 새로 만들어지지 않고 그대로 살아 있어야
      // 그 안의 HighlightShortformDraft 설정·체크 상태가 유지된다.
      const before = fixture.nativeElement.querySelector('app-dialog-result-detail');
      expect(before).not.toBeNull();

      let loadingDuringRefetch: boolean | null = null;
      projects.getDetail.and.callFake(async () => {
        loadingDuringRefetch = component.loading();
        return detail;
      });

      await component.onTrimSave({ clip, range: { startSec: 5, endSec: 32 } });
      fixture.detectChanges();

      expect(loadingDuringRefetch).toBeFalse();
      expect(component.loading()).toBeFalse();
      expect(fixture.nativeElement.querySelector('app-dialog-result-detail')).toBe(before);
    });

    it('저장해도 보던 클립에 머무르고, 리로드될 플레이어를 그 시작점으로 되돌린다', async () => {
      const component = fixture.componentInstance;
      const clips = [{ clipId: '0', title: 'clip 1', durationSec: 20, videoPath: '/tmp/c0.mp4' }, dialogDetail.clips[0]];
      const detail = { ...dialogDetail, clips };
      component.detail.set(detail);
      projects.getDetail.and.resolveTo(detail);
      component.selectedClipId.set('1');

      await component.onTrimSave({ clip: clips[1], range: { startSec: 5, endSec: 32 } });

      // 첫 클립으로 튀면 트리머가 닫히고 방금 자른 결과를 볼 자리를 잃는다
      expect(component.selectedClipId()).toBe('1');
      // 새 mediaToken으로 src가 바뀌어 플레이어가 0:00으로 돌아가므로 위치를 되살려 준다
      expect(component.restoreSeek()?.sec).toBe(5);
    });

    it('같은 시작점으로 다시 저장해도 복원 신호가 새로 간다 — seq가 없으면 값이 같아 무시된다', async () => {
      const component = fixture.componentInstance;
      component.detail.set(dialogDetail);
      projects.getDetail.and.resolveTo(dialogDetail);

      await component.onTrimSave({ clip: dialogDetail.clips[0], range: { startSec: 5, endSec: 32 } });
      const first = component.restoreSeek();
      await component.onTrimSave({ clip: dialogDetail.clips[0], range: { startSec: 5, endSec: 30 } });

      expect(component.restoreSeek()?.sec).toBe(5);
      expect(component.restoreSeek()?.seq).not.toBe(first?.seq);
    });

    it('손잡이가 양 끝이면 되돌리기로 보낸다 — 길이 비교를 서버로 넘기지 않는다', async () => {
      const component = fixture.componentInstance;
      const clip = { ...dialogDetail.clips[0], originalDurationSec: 39, trim: { startSec: 5, endSec: 32 } };
      component.detail.set({ ...dialogDetail, clips: [clip] });

      await component.onTrimSave({ clip, range: { startSec: 0, endSec: 39 } });

      expect(projects.revertClipTrim).toHaveBeenCalledWith('project-dialog', '1');
      expect(projects.trimClip).not.toHaveBeenCalled();
    });

    it('저장이 실패해도 잠금은 풀리고 토스트가 뜬다', async () => {
      const component = fixture.componentInstance;
      component.detail.set(dialogDetail);
      projects.trimClip.and.rejectWith(new Error('ffmpeg 실패'));

      await component.onTrimSave({ clip: dialogDetail.clips[0], range: { startSec: 5, endSec: 32 } });

      expect(component.trimmingClipId()).toBeNull();
      expect(notify.showToast).toHaveBeenCalled();
    });

    it('이미 저장 중이면 두 번째 요청은 무시한다', async () => {
      const component = fixture.componentInstance;
      component.detail.set(dialogDetail);
      component.trimmingClipId.set('1');

      await component.onTrimSave({ clip: dialogDetail.clips[0], range: { startSec: 5, endSec: 32 } });

      expect(projects.trimClip).not.toHaveBeenCalled();
    });
  });

  // 클립 오버레이 ②: 헤더의 "13 / 24"는 오버레이가 새로 계산하지 않고 이 컴포넌트가 이미
  // 들고 있는 clipOverlayIds/clipOverlayId에서 구한 값을 그대로 input으로 받는다.
  describe('클립 오버레이 위치 표시 + 순환', () => {
    it('overlayClipIndex는 clipOverlayIds에서 현재 클립의 1-based 위치, overlayClipCount는 전체 개수다', () => {
      const component = fixture.componentInstance;
      component.clipOverlayIds.set(['c1', 'c2', 'c3']);
      component.clipOverlayId.set('c2');

      expect(component.overlayClipIndex()).toBe(2);
      expect(component.overlayClipCount()).toBe(3);
    });

    it('clipOverlayId가 clipOverlayIds에 없으면(불일치) 위치가 없다', () => {
      const component = fixture.componentInstance;
      component.clipOverlayIds.set(['c1', 'c2']);
      component.clipOverlayId.set('not-in-list');

      expect(component.overlayClipIndex()).toBeNull();
    });

    it('마지막 클립에서 다음으로 넘기면 처음으로 돌아간다(순환 유지)', () => {
      const component = fixture.componentInstance;
      component.clipOverlayIds.set(['c1', 'c2', 'c3']);
      component.clipOverlayId.set('c3');

      component.showNextOverlayClip();

      expect(component.clipOverlayId()).toBe('c1');
    });
  });

  describe('원본 비율 클립 준비 대기 폴링(T13 D5)', () => {
    const pendingDetail: ProjectDetail = {
      ...danceDetail,
      projectId: 'project-dialog',
      category: 'dialog',
      clips: [
        { clipId: '1', title: 'clip', durationSec: 5, rawStatus: 'pending' },
        { clipId: '2', title: 'clip 2', durationSec: 5, rawStatus: 'ready' },
      ],
    };
    const readyDetail: ProjectDetail = {
      ...pendingDetail,
      clips: pendingDetail.clips.map((clip) => ({ ...clip, rawStatus: 'ready' as const })),
    };

    async function flush(): Promise<void> {
      for (let i = 0; i < 10; i++) await Promise.resolve();
    }

    beforeEach(() => {
      jasmine.clock().install();
      // 경과 시간(2분·10분)은 Date.now로 잰다 — tick과 함께 가게 한다.
      jasmine.clock().mockDate(new Date('2026-09-18T00:00:00Z'));
    });
    afterEach(() => jasmine.clock().uninstall());

    it('2분 넘게 계속 준비 중이면 15초 간격으로 늦춘다', async () => {
      fixture.componentInstance.detail.set(pendingDetail);
      projects.getDetail.and.resolveTo(pendingDetail);
      fixture.detectChanges();

      for (let i = 0; i < 40; i++) {
        jasmine.clock().tick(3000);
        await flush();
      }
      expect(projects.getDetail).toHaveBeenCalledTimes(40);

      jasmine.clock().tick(3000);
      await flush();
      expect(projects.getDetail).toHaveBeenCalledTimes(40);
      jasmine.clock().tick(12000);
      await flush();
      expect(projects.getDetail).toHaveBeenCalledTimes(41);
      expect(snackBar.open).not.toHaveBeenCalled();
    });

    it('10분 넘게 계속 준비 중이면 멈추고 다시 열어 달라고 알린다', async () => {
      fixture.componentInstance.detail.set(pendingDetail);
      projects.getDetail.and.resolveTo(pendingDetail);
      fixture.detectChanges();

      for (let elapsed = 0; elapsed < 10 * 60 * 1000; elapsed += 3000) {
        jasmine.clock().tick(3000);
        await flush();
      }
      fixture.detectChanges();
      expect(snackBar.open).toHaveBeenCalledOnceWith(
        '원본 비율 클립 준비가 오래 걸리고 있어요. 잠시 후 다시 열어 주세요', '닫기', jasmine.any(Object));
      const calls = projects.getDetail.calls.count();

      jasmine.clock().tick(60000);
      await flush();
      expect(projects.getDetail).toHaveBeenCalledTimes(calls);
      expect(fixture.componentInstance.detail()).toBe(pendingDetail);
    });

    it('준비 중 클립이 있으면 3초마다 조용히 다시 불러오고, 다 준비되면 멈춘다', async () => {
      const component = fixture.componentInstance;
      component.detail.set(pendingDetail);
      component.selectedClipId.set('2');
      projects.getDetail.and.resolveTo(pendingDetail);
      fixture.detectChanges();

      jasmine.clock().tick(2999);
      expect(projects.getDetail).not.toHaveBeenCalled();
      jasmine.clock().tick(1);
      await flush();
      expect(projects.getDetail).toHaveBeenCalledOnceWith('project-dialog');
      // 조용한 새로고침 — 보던 클립을 그대로 둔다
      expect(component.selectedClipId()).toBe('2');
      expect(component.loading()).toBeFalse();

      projects.getDetail.and.resolveTo(readyDetail);
      jasmine.clock().tick(3000);
      await flush();
      fixture.detectChanges();
      expect(projects.getDetail).toHaveBeenCalledTimes(2);

      jasmine.clock().tick(9000);
      await flush();
      expect(projects.getDetail).toHaveBeenCalledTimes(2);
    });

    it('폴링 실패는 조용히 — 상세·에러를 그대로 두고 다음 틱에 다시 묻는다', async () => {
      const component = fixture.componentInstance;
      component.detail.set(pendingDetail);
      component.selectedClipId.set('1');
      fixture.detectChanges();
      const errorBefore = component.error();
      projects.getDetail.and.rejectWith(new Error('down'));

      jasmine.clock().tick(3000);
      await flush();
      fixture.detectChanges();
      expect(component.detail()).toBe(pendingDetail);
      expect(component.error()).toBe(errorBefore);

      jasmine.clock().tick(3000);
      await flush();
      expect(projects.getDetail).toHaveBeenCalledTimes(2);
      expect(snackBar.open).not.toHaveBeenCalled();
    });

    it('연달아 5번 실패하면 멈추고 스낵바로 알린다', async () => {
      const component = fixture.componentInstance;
      component.detail.set(pendingDetail);
      fixture.detectChanges();
      projects.getDetail.and.rejectWith(new Error('down'));

      for (let i = 0; i < 5; i++) {
        jasmine.clock().tick(3000);
        await flush();
      }
      fixture.detectChanges();
      expect(projects.getDetail).toHaveBeenCalledTimes(5);
      expect(snackBar.open).toHaveBeenCalledOnceWith('원본 비율 클립 상태를 확인하지 못했어요', '닫기', jasmine.any(Object));
      expect(component.detail()).toBe(pendingDetail);

      jasmine.clock().tick(15000);
      await flush();
      expect(projects.getDetail).toHaveBeenCalledTimes(5);
    });

    it('준비 중 클립이 없으면 폴링하지 않는다', async () => {
      fixture.componentInstance.detail.set(readyDetail);
      fixture.detectChanges();
      jasmine.clock().tick(9000);
      await flush();
      expect(projects.getDetail).not.toHaveBeenCalled();
    });

    it('화면을 떠나면 멈춘다', async () => {
      fixture.componentInstance.detail.set(pendingDetail);
      projects.getDetail.and.resolveTo(pendingDetail);
      fixture.detectChanges();
      fixture.destroy();
      jasmine.clock().tick(9000);
      await flush();
      expect(projects.getDetail).not.toHaveBeenCalled();
    });
  });
  describe('숏폼 카드 [편집] 복원(?fromShortform, T13)', () => {
    const saved: HighlightShortformSettings = {
      templateId: 'preset-a', topTitle: '저장 위', bottomTitle: '저장 아래', sourceCredit: '출처: 저장',
      bgmAssetId: null, sourceAudioEnabled: false,
      transition: { enabled: true, effects: ['fade', 'circleclose'], seed: 9 },
    };
    const restoreDance: ProjectDetail = {
      ...danceDetail,
      clips: [
        { clipId: 'c1', title: '1', durationSec: 2, personId: 'person_1' },
        { clipId: 'c2', title: '2', durationSec: 2, personId: 'person_1' },
        { clipId: 'c3', title: '3', durationSec: 2, personId: 'sakura' },
      ],
      // 기본 선택은 확정 멤버(sakura) — 복원이 person_1로 바꿔야 한다.
      persons: [
        { personId: 'person_1', personName: 'person 1', mappedMember: false, clipIds: ['c1', 'c2'] },
        { personId: 'sakura', personName: '사쿠라', mappedMember: true, clipIds: ['c3'] },
      ],
    };
    const restoreDialog: ProjectDetail = {
      ...danceDetail,
      projectId: 'project-dialog',
      pluginName: 'dialog_highlight',
      category: 'dialog',
      clips: [
        { clipId: 'd1', title: '1', durationSec: 4 },
        { clipId: 'd2', title: '2', durationSec: 4 },
      ],
    };
    const restorePerson: ProjectDetail = {
      ...danceDetail,
      projectId: 'project-person', pluginName: 'person_highlight', category: 'person',
      clips: [
        { clipId: 's1', title: '1', durationSec: 3, sourceStartSec: 10, sourceEndSec: 13, personIds: ['p1'] },
        { clipId: 's2', title: '2', durationSec: 4, sourceStartSec: 20, sourceEndSec: 24, personIds: ['p1'] },
        { clipId: 's3', title: '3', durationSec: 4, sourceStartSec: 30, sourceEndSec: 34, personIds: ['p1'], excluded: true },
        { clipId: 's4', title: '4', durationSec: 4, sourceStartSec: 40, sourceEndSec: 44, personIds: ['p1'] },
      ],
      persons: [{ personId: 'p1', personName: 'Person 1', clipIds: ['s1', 's2', 's3', 's4'] }],
    };

    function manifestWith(request: unknown) {
      return { projectId: 'render-project', detail: { editState: { highlightShortform: request } } };
    }
    function snapshotWith(request: unknown) {
      return { projectId: 'render-project', jobId: 'hls_1', params: { render_manifest: manifestWith(request) } };
    }
    function danceRequest(clipIds: string[], projectId = 'project-dance') {
      return { origin: { kind: 'dance', projectId, personId: 'person_1' }, clipIds, settings: saved };
    }
    function dialogRequest(clipIds: string[]) {
      return { origin: { kind: 'dialog', projectId: 'project-dialog' }, clipIds, settings: saved };
    }
    function personRequest(clipIds: string[]) {
      return { origin: { kind: 'person', projectId: 'project-person', personId: 'p1' }, clipIds, settings: saved };
    }

    async function open(detail: ProjectDetail): Promise<ProjectsDetailPageComponent> {
      routeParams = { projectId: detail.projectId };
      routeQuery = { fromShortform: 'hls_1' };
      projects.getDetail.and.resolveTo(detail);
      const component = fixture.componentInstance;
      await component.ngOnInit();
      return component;
    }

    const clearQuery = () => jasmine.objectContaining({
      queryParams: { fromShortform: null },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });

    it('복원 요청 동안 restoring이 켜지고(체크·설정 칸 잠금), 끝나면 풀린다', async () => {
      let finish!: (value: unknown) => void;
      projects.getByJob.and.returnValue(new Promise((resolve) => { finish = resolve; }));
      routeParams = { projectId: restoreDance.projectId };
      routeQuery = { fromShortform: 'hls_1' };
      projects.getDetail.and.resolveTo(restoreDance);
      const component = fixture.componentInstance;
      const init = component.ngOnInit();
      await new Promise((resolve) => setTimeout(resolve, 0));
      expect(component.restoring()).toBeTrue();
      fixture.detectChanges();
      const dance = fixture.debugElement.query(By.directive(DanceResultDetailComponent))
        .componentInstance as DanceResultDetailComponent;
      expect(dance.actionsDisabled()).toBeTrue();
      expect(fixture.nativeElement.querySelector('app-shortform-info-panel').hasAttribute('inert')).toBeTrue();
      finish(snapshotWith(danceRequest(['c2'])));
      await init;
      fixture.detectChanges();
      expect(component.restoring()).toBeFalse();
      expect(dance.actionsDisabled()).toBeFalse();
      expect(fixture.nativeElement.querySelector('app-shortform-info-panel').hasAttribute('inert')).toBeFalse();
    });

    it('복원이 실패해도 잠금이 풀린다', async () => {
      projects.getByJob.and.rejectWith(new Error('x'));
      const component = await open(restoreDance);
      expect(component.restoring()).toBeFalse();
    });

    it('쿼리가 없으면 작업을 찾지 않는다', async () => {
      routeParams = { projectId: 'project-dance' };
      projects.getDetail.and.resolveTo(restoreDance);
      await fixture.componentInstance.ngOnInit();

      expect(projects.getByJob).not.toHaveBeenCalled();
      expect(router.navigate).not.toHaveBeenCalled();
    });

    it('안무: 그 인물을 고르고 저장된 clipIds·설정을 결과 화면에 넘기며, 쿼리를 지운다', async () => {
      projects.getByJob.and.resolveTo(snapshotWith(danceRequest(['c2'])));
      const component = await open(restoreDance);

      expect(projects.getByJob).toHaveBeenCalledOnceWith('hls_1');
      expect(component.selectedPersonId()).toBe('person_1');
      expect(component.shortformRestore()).toEqual({ clipIds: ['c2'], settings: saved });
      expect(router.navigate).toHaveBeenCalledOnceWith([], clearQuery());
      expect(snackBar.open).not.toHaveBeenCalled();

      // 결과 화면까지 이어지는지 — 체크가 정확히 c2만.
      fixture.detectChanges();
      const dance = fixture.debugElement.query(By.directive(DanceResultDetailComponent))
        .componentInstance as DanceResultDetailComponent;
      expect(dance.checkedClips().map((clip) => clip.clipId)).toEqual(['c2']);
    });

    it('안무: 컷 전환 설정이 없는 옛 저장본은 기본값(켬·9종 전부)으로 되살린다', async () => {
      const { transition: _none, ...oldSettings } = saved;
      projects.getByJob.and.resolveTo(snapshotWith({ ...danceRequest(['c2']), settings: oldSettings }));
      const component = await open(restoreDance);

      expect(component.shortformRestore()?.settings).toEqual({
        ...saved,
        transition: { enabled: true, effects: [...CUT_TRANSITION_EFFECTS], seed: jasmine.any(Number) as unknown as number },
      });
    });

    it('안무: 사라진(숨긴) 클립은 빼고 나머지만 — 스낵바로 알린다', async () => {
      projects.getByJob.and.resolveTo(snapshotWith(danceRequest(['c2', 'gone', 'c3'])));
      const component = await open(restoreDance);

      expect(component.shortformRestore()?.clipIds).toEqual(['c2']);
      expect(snackBar.open).toHaveBeenCalledOnceWith(
        '일부 클립이 없어져 나머지만 불러왔어요', '닫기', jasmine.objectContaining({ duration: 4000 }));
    });

    it('대사: 그 클립을 고르고 설정(타이틀 포함)을 넘긴다', async () => {
      projects.getByJob.and.resolveTo(snapshotWith(dialogRequest(['d2'])));
      const component = await open(restoreDialog);

      expect(component.selectedClipId()).toBe('d2');
      expect(component.shortformRestore()).toEqual({ clipIds: ['d2'], settings: saved });
      expect(snackBar.open).not.toHaveBeenCalled();
    });

    it('인물: 체크한 장면 여러 개와 설정을 복원하고 제외된 장면은 뺀다', async () => {
      projects.getByJob.and.resolveTo(snapshotWith(personRequest(['s2', 's1', 's3'])));
      const component = await open(restorePerson);
      expect(component.selectedPersonId()).toBe('p1');
      expect(component.selectedClipId()).toBe('s2');
      expect(component.shortformRestore()).toEqual({ clipIds: ['s2', 's1'], settings: saved });
    });

    it('대사: 클립이 사라졌으면 기본 선택은 두고 공통 설정만 — 설정만 불러왔다고 알린다', async () => {
      projects.getByJob.and.resolveTo(snapshotWith(dialogRequest(['gone'])));
      const component = await open(restoreDialog);

      expect(component.selectedClipId()).toBe('d1');
      expect(component.shortformRestore()).toEqual({ clipIds: [], settings: saved });
      expect(snackBar.open).toHaveBeenCalledOnceWith(
        '저장된 클립을 찾지 못해 설정만 불러왔어요', '닫기', jasmine.objectContaining({ duration: 4000 }));
    });

    it('안무: 클립이 하나도 안 남았으면 설정만 불러왔다고 알린다', async () => {
      projects.getByJob.and.resolveTo(snapshotWith(danceRequest(['gone', 'gone2'])));
      const component = await open(restoreDance);

      expect(component.shortformRestore()?.clipIds).toEqual([]);
      expect(snackBar.open).toHaveBeenCalledOnceWith(
        '저장된 클립을 찾지 못해 설정만 불러왔어요', '닫기', jasmine.objectContaining({ duration: 4000 }));
    });

    it('작업 스냅샷에 manifest가 없으면 렌더 프로젝트 manifest에서 꺼낸다', async () => {
      projects.getByJob.and.resolveTo({ projectId: 'render-project', jobId: 'hls_1', params: {} });
      projects.getManifest.and.resolveTo(manifestWith(danceRequest(['c1'])));
      const component = await open(restoreDance);

      expect(projects.getManifest).toHaveBeenCalledOnceWith('render-project');
      expect(component.shortformRestore()?.clipIds).toEqual(['c1']);
    });

    it('아직 프로젝트가 아닌 작업(대기·렌더 중)은 작업 목록의 params에서 꺼낸다', async () => {
      jobs.jobs.set([{ jobId: 'hls_1', params: { render_manifest: manifestWith(danceRequest(['c1'])) } }]);
      const component = await open(restoreDance);

      expect(component.shortformRestore()?.clipIds).toEqual(['c1']);
    });

    it('모르는 jobId는 조용히 무시한다(기록만) — 쿼리는 지운다', async () => {
      const component = await open(restoreDance);

      expect(component.shortformRestore()).toBeNull();
      expect(component.selectedPersonId()).toBe('sakura');
      expect(component.error()).toBeNull();
      expect(snackBar.open).not.toHaveBeenCalled();
      expect(notify.showToast).not.toHaveBeenCalled();
      expect(TestBed.inject(RendererLogger).log).toHaveBeenCalled();
      expect(router.navigate).toHaveBeenCalledOnceWith([], clearQuery());
    });

    it('다른 프로젝트에서 만든 숏폼이면 무시한다', async () => {
      projects.getByJob.and.resolveTo(snapshotWith(danceRequest(['c2'], 'other-project')));
      const component = await open(restoreDance);

      expect(component.shortformRestore()).toBeNull();
      expect(component.selectedPersonId()).toBe('sakura');
      expect(snackBar.open).not.toHaveBeenCalled();
    });
  });
});
