import { navHelpFor } from './nav-help-content';
import type { NavHelp } from './nav-help';

export type PluginFeatureName =
  | 'proof_new_plugin'
  | 'shortform_url'
  | 'shortform_paste'
  | 'shortform_prompt'
  | 'shortform_explainer'
  | 'shortform_article'
  | 'shortform_director'
  | 'dance_highlight'
  | 'person_highlight'
  | 'dialog_highlight'
  | 'comment_overlay'
  | 'variation'
  | 'ranking'
  | 'curation'
  | 'overseas_dub';

export type ShellNavigationName =
  | 'projects'
  | 'templates'
  | 'store'
  | 'assets'
  | 'youtube_debug'
  | 'logs'
  | 'error_simulation'
  | 'dashboard'
  | 'settings';

export type AppNavigationName = PluginFeatureName | ShellNavigationName;

export type AppNavigationKind = 'plugin' | 'shell';

interface BaseNavigationDefinition<
  Name extends AppNavigationName,
  Kind extends AppNavigationKind,
> {
  readonly name: Name;
  readonly kind: Kind;
  readonly label: string;
  readonly navLabel?: string;
  readonly pageTitle?: string;
  readonly subtitle?: string;
  readonly icon: string;
  readonly route: string;
  readonly devOnly?: boolean;
}

interface PluginNavigationDefinition<Name extends PluginFeatureName = PluginFeatureName>
  extends BaseNavigationDefinition<Name, 'plugin'> {
  readonly storeDisplayName?: string;
  readonly storeName?: string;
}

interface ShellNavigationDefinition<Name extends ShellNavigationName = ShellNavigationName>
  extends BaseNavigationDefinition<Name, 'shell'> {}

interface BaseNavigationMetadata<
  Name extends AppNavigationName,
  Kind extends AppNavigationKind,
> {
  readonly name: Name;
  readonly kind: Kind;
  readonly label: string;
  readonly navLabel: string;
  readonly pageTitle: string;
  readonly subtitle: string;
  readonly icon: string;
  readonly route: string;
  readonly devOnly?: boolean;
  /**
   * 좌측 nav 도움말 카드. 문구는 여기 적지 않는다 — `nav-help-content.ts`가 단일 출처이고
   * 아래 팩토리가 이름으로 찾아 붙인다. 문구가 없는 항목은 `undefined`(카드 안 뜸).
   */
  readonly help?: NavHelp;
}

export interface PluginNavigationMetadata<Name extends PluginFeatureName = PluginFeatureName>
  extends BaseNavigationMetadata<Name, 'plugin'> {
  readonly storeDisplayName: string;
  readonly storeName: string;
}

export interface ShellNavigationMetadata<Name extends ShellNavigationName = ShellNavigationName>
  extends BaseNavigationMetadata<Name, 'shell'> {}

export type AppNavigationMetadata =
  | PluginNavigationMetadata
  | ShellNavigationMetadata;

type AppNavigationMetadataMap = Readonly<{
  [Name in PluginFeatureName]: PluginNavigationMetadata<Name>;
} & {
  [Name in ShellNavigationName]: ShellNavigationMetadata<Name>;
}>;

export type NavGroupId = 'highlight' | 'autoMake' | 'editVariant' | 'compose';

export interface NavGroupDefinition {
  readonly id: NavGroupId;
  readonly label: string;
  /** 묶음 안 순서 그대로 메뉴에 선다. */
  readonly members: readonly PluginFeatureName[];
}

/**
 * 좌측 메뉴 묶음(spec D2) — **하는 일** 기준 4개. 가진 재료("영상이 있을 때")로 묶지 않는다.
 * 묶음 순서가 곧 nav와 스토어 목록의 순서다(아래 `PLUGIN_FEATURE_ORDER`가 여기서 나온다).
 */
export const NAV_GROUPS: readonly NavGroupDefinition[] = [
  { id: 'highlight', label: '하이라이트 추출', members: ['dialog_highlight', 'dance_highlight', 'person_highlight'] },
  {
    id: 'autoMake',
    label: '영상 자동제작',
    members: ['shortform_url', 'shortform_paste', 'shortform_prompt', 'shortform_explainer', 'shortform_article', 'overseas_dub'],
  },
  { id: 'editVariant', label: '영상 편집·변형', members: ['variation', 'comment_overlay'] },
  { id: 'compose', label: '영상 구성', members: ['shortform_director', 'ranking', 'curation'] },
];

/** 묶음이 정해지지 않은 새 플러그인이 붙는 맨 뒤 묶음(spec D10). */
export const NAV_OTHER_GROUP_LABEL = '그 밖의 기능';

/**
 * 좌측 nav 워크플로와 스토어 목록이 함께 따르는 **단일** 표시 순서 = 묶음 순서(spec D14).
 * 따로 적어 두면 묶음 순서와 두 벌이 된다.
 */
export const PLUGIN_FEATURE_ORDER: readonly PluginFeatureName[] = NAV_GROUPS.flatMap((group) => group.members);

export type ShortformInputMode = 'url' | 'paste' | 'prompt' | 'article' | 'explainer';

/** 숏폼 입력 방식 → 그 방식의 메뉴(기능) 이름. 홈 카드·큐·크레딧 확인창이 메뉴 이름을 고를 때 쓴다. */
export function shortformFeatureForMode(mode: ShortformInputMode): PluginFeatureName {
  return `shortform_${mode}`;
}

/** nav 최상단 = 앱의 홈. 워크플로들보다 위에 온다. */
export const TOP_SHELL_NAVIGATION_ORDER: readonly ShellNavigationName[] = [
  'projects',
];

/**
 * 템플릿(빌더)은 여기서 뺐다(T5) — `/assets?kind=template`(소재 관리 "템플릿" 종류)이
 * 새 진입점이고, 편집기(`/templates` 라우트)는 거기서 "편집기 열기"/"새 템플릿"으로만
 * 연다. `APP_NAVIGATION_METADATA.templates`는 남긴다 — 빌더 페이지 헤더가 그 제목·부제·
 * 아이콘(`shellPageTitle`/`shellPageSubtitle`/`shellPageIcon`)을 계속 쓴다. 이 배열이
 * 비면 좌측 nav가 이 그룹 자리에 빈 구분선을 남기지 않도록 `nav.component.html`도 함께
 * 고쳤다.
 */
export const PRIMARY_SHELL_NAVIGATION_ORDER: readonly ShellNavigationName[] = [];

export const STORE_SHELL_NAVIGATION_ORDER: readonly ShellNavigationName[] = [
  'store',
];

export const UTILITY_SHELL_NAVIGATION_ORDER: readonly ShellNavigationName[] = [
  'assets',
  'youtube_debug',
  'logs',
  'error_simulation',
  'dashboard',
  'settings',
];

export const APP_NAVIGATION_METADATA = {
  proof_new_plugin: pluginMetadata({ name: 'proof_new_plugin', kind: 'plugin', label: '실험용 새 등록', icon: 'science', route: 'proof/new' }),
  shortform_url: pluginMetadata({
    name: 'shortform_url',
    kind: 'plugin',
    label: '블로그 to 숏폼',
    icon: 'link',
    route: 'shortform/url',
  }),
  shortform_paste: pluginMetadata({
    name: 'shortform_paste',
    kind: 'plugin',
    label: '텍스트 to 숏폼',
    icon: 'article',
    route: 'shortform/paste',
  }),
  shortform_prompt: pluginMetadata({
    name: 'shortform_prompt',
    kind: 'plugin',
    label: '프롬프트 to 숏폼',
    icon: 'lightbulb',
    route: 'shortform/prompt',
  }),
  shortform_explainer: pluginMetadata({
    name: 'shortform_explainer',
    kind: 'plugin',
    label: '설명 to 숏폼',
    icon: 'auto_awesome',
    route: 'shortform/explainer',
  }),
  shortform_article: pluginMetadata({
    name: 'shortform_article',
    kind: 'plugin',
    label: '매체기사 to 숏폼',
    icon: 'newspaper',
    route: 'shortform/article',
  }),
  overseas_dub: pluginMetadata({
    name: 'overseas_dub',
    kind: 'plugin',
    label: '해외영상 to 숏폼',
    subtitle: '해외 상품 소개 영상을 한국어 숏폼으로 바꿔요.',
    icon: 'translate',
    route: 'overseas-dub',
  }),
  shortform_director: pluginMetadata({
    name: 'shortform_director',
    kind: 'plugin',
    label: '스토리보드',
    storeName: 'storyboard',
    subtitle: '프로필에 맞는 주제와 시나리오를 제안해 다음 영상을 기획하도록 돕습니다. 대본과 이미지·영상 검색어, AI 생성 프롬프트를 함께 제공합니다.',
    icon: 'view_carousel',
    route: 'shortform/director',
  }),
  dance_highlight: pluginMetadata({
    name: 'dance_highlight',
    kind: 'plugin',
    label: '안무 하이라이트',
    subtitle: '영상에서 아티스트와 멤버별 안무 하이라이트를 추출합니다.',
    icon: 'taunt',
    route: 'dance',
  }),
  person_highlight: pluginMetadata({
    name: 'person_highlight', kind: 'plugin', label: '인물 하이라이트',
    subtitle: '영상에 등장한 사람의 장면을 찾고 검토합니다.',
    icon: 'groups', route: 'person',
  }),
  dialog_highlight: pluginMetadata({
    name: 'dialog_highlight',
    kind: 'plugin',
    label: '대사 하이라이트',
    subtitle: '영상에서 대사 흐름, 장면 전환, 음성 변화를 함께 분석해 하이라이트 구간을 추출합니다.',
    icon: 'format_quote',
    route: 'dialog',
  }),
  comment_overlay: pluginMetadata({
    name: 'comment_overlay',
    kind: 'plugin',
    label: '댓글 오버레이',
    subtitle: '영상에 시청자 댓글을 얹어 새 영상으로 내보냅니다.',
    icon: 'chat',
    route: 'comment-overlay',
  }),
  variation: pluginMetadata({
    name: 'variation',
    kind: 'plugin',
    label: '1N : 숏폼 베리에이션',
    icon: 'dynamic_feed',
    route: 'variation',
  }),
  ranking: pluginMetadata({
    name: 'ranking',
    kind: 'plugin',
    label: '영상 랭킹',
    subtitle: '순위별 클립을 넣어 TOP N 카운트다운 쇼츠를 만듭니다.',
    icon: 'trophy',
    route: 'ranking',
  }),
  curation: pluginMetadata({
    name: 'curation',
    kind: 'plugin',
    label: '상품 큐레이션',
    subtitle: '쇼핑몰 순위로 소개 영상',
    icon: 'shopping_bag',
    route: 'curation',
  }),
  projects: shellMetadata({
    name: 'projects',
    kind: 'shell',
    label: '홈',
    pageTitle: '프로젝트 보관함',
    subtitle: '실행 중인 큐와 완료된 프로젝트를 확인합니다.',
    icon: 'home',
    route: 'projects',
  }),
  templates: shellMetadata({
    name: 'templates',
    kind: 'shell',
    label: '템플릿',
    subtitle: '숏폼 렌더에 쓰이는 자막·레이아웃 템플릿을 만들고 편집합니다.',
    icon: 'view_quilt',
    route: 'templates',
  }),
  store: shellMetadata({
    name: 'store',
    kind: 'shell',
    label: '스토어',
    pageTitle: '플러그인 스토어',
    subtitle: '설치된 플러그인을 확인하고 작업 화면을 엽니다.',
    icon: 'storefront',
    route: 'store',
  }),
  assets: shellMetadata({
    name: 'assets',
    kind: 'shell',
    label: '소재 관리',
    subtitle: '영상 제작에 쓰이는 클립·소리를 한곳에서 관리합니다.',
    icon: 'perm_media',
    route: 'assets',
  }),
  youtube_debug: shellMetadata({
    name: 'youtube_debug',
    kind: 'shell',
    label: 'YouTube 디버그',
    pageTitle: 'YouTube 인증 디버그',
    subtitle: '쿠키와 yt-dlp 인증 경로를 비교합니다.',
    icon: 'cookie',
    route: 'youtube-debug',
    devOnly: true,
  }),
  logs: shellMetadata({
    name: 'logs',
    kind: 'shell',
    label: '로그',
    pageTitle: '디버그 로그',
    subtitle: 'main · renderer · nest · python 통합',
    icon: 'terminal',
    route: 'logs',
    devOnly: true,
  }),
  error_simulation: shellMetadata({
    name: 'error_simulation',
    kind: 'shell',
    label: '에러 시뮬레이션',
    pageTitle: '에러 시뮬레이션',
    subtitle: '영상 불러오기를 실패시켜 에러 배너를 실물로 확인합니다.',
    icon: 'bug_report',
    route: 'error-simulation',
    devOnly: true,
  }),
  dashboard: shellMetadata({
    name: 'dashboard',
    kind: 'shell',
    label: '대시보드',
    pageTitle: '플러그인 대시보드',
    subtitle: '로컬 런타임 리소스와 플러그인 실행 상태를 확인합니다.',
    icon: 'dashboard',
    route: 'dashboard',
    // 운영자 진단용이라 평소엔 감춘다 — 이걸 빼면 소재 관리와 설정이 nav에서 붙는다.
    devOnly: true,
  }),
  settings: shellMetadata({
    name: 'settings',
    kind: 'shell',
    label: '설정',
    subtitle: '앱 환경과 계정·크레딧을 관리합니다.',
    icon: 'settings',
    route: 'settings',
  }),
} satisfies AppNavigationMetadataMap;

export function appNavigationMetadata(name: string): AppNavigationMetadata | null {
  return isAppNavigationName(name) ? APP_NAVIGATION_METADATA[name] : null;
}

export function appNavigationItems(
  names: readonly AppNavigationName[],
): readonly AppNavigationMetadata[] {
  return names.map((name) => APP_NAVIGATION_METADATA[name]);
}

export function pluginFeatureMetadata(name: string): PluginNavigationMetadata | null {
  const metadata = appNavigationMetadata(name);
  return metadata?.kind === 'plugin' ? metadata : null;
}

export function pluginFeatureNavigation(name: PluginFeatureName): PluginNavigationMetadata {
  return APP_NAVIGATION_METADATA[name];
}

export function pluginRouteForName(name: string): string | undefined {
  const route = pluginFeatureMetadata(name)?.route;
  return route ? `/${route}` : undefined;
}

export function pluginStoreDisplayName(name: PluginFeatureName): string {
  return APP_NAVIGATION_METADATA[name].storeDisplayName;
}

export function knownPluginStoreDisplayName(name: string): string | null {
  return pluginFeatureMetadata(name)?.storeDisplayName ?? null;
}

export function knownPluginStoreName(name: string): string {
  return pluginFeatureMetadata(name)?.storeName ?? name;
}

export function pluginNavLabel(name: PluginFeatureName): string {
  return APP_NAVIGATION_METADATA[name].navLabel;
}

export function pluginPageTitle(name: PluginFeatureName): string {
  return APP_NAVIGATION_METADATA[name].pageTitle;
}

export function pluginPageSubtitle(name: PluginFeatureName): string {
  return APP_NAVIGATION_METADATA[name].subtitle;
}

export function shellPageTitle(name: ShellNavigationName): string {
  return APP_NAVIGATION_METADATA[name].pageTitle;
}

export function shellPageSubtitle(name: ShellNavigationName): string {
  return APP_NAVIGATION_METADATA[name].subtitle;
}

/** 좌측 nav가 쓰는 아이콘과 같은 값 — 페이지 헤더 좌측 아이콘 배선용. */
export function shellPageIcon(name: ShellNavigationName): string {
  return APP_NAVIGATION_METADATA[name].icon;
}

/** 좌측 nav가 쓰는 아이콘과 같은 값 — 페이지 헤더 좌측 아이콘 배선용. */
export function pluginPageIcon(name: PluginFeatureName): string {
  return APP_NAVIGATION_METADATA[name].icon;
}

function isAppNavigationName(name: string): name is AppNavigationName {
  return Object.prototype.hasOwnProperty.call(APP_NAVIGATION_METADATA, name);
}

function pluginMetadata<Name extends PluginFeatureName>(
  definition: PluginNavigationDefinition<Name>,
): PluginNavigationMetadata<Name> {
  return {
    ...definition,
    navLabel: definition.navLabel ?? definition.label,
    pageTitle: definition.pageTitle ?? definition.label,
    subtitle: definition.subtitle ?? '',
    storeDisplayName: definition.storeDisplayName ?? definition.label,
    storeName: definition.storeName ?? definition.name,
    help: navHelpFor(definition.name) ?? undefined,
  };
}

function shellMetadata<Name extends ShellNavigationName>(
  definition: ShellNavigationDefinition<Name>,
): ShellNavigationMetadata<Name> {
  return {
    ...definition,
    navLabel: definition.navLabel ?? definition.label,
    pageTitle: definition.pageTitle ?? definition.label,
    subtitle: definition.subtitle ?? '',
    help: navHelpFor(definition.name) ?? undefined,
  };
}
