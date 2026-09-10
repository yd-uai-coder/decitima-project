// DeciTima samples │ 初出 Phase 3 │ 改訂 Phase 4,5,6,7
export type MenuLeaf = { label: string; href: string };
export type MenuGroup = { label: string; children: MenuLeaf[] };

// (pages)/(sample)配下の実際のディレクトリ階層(data/form-parts/gallery/layout/others)を
// そのまま反映している。ラベルは各ページのBreadcrumb pageTitleに合わせており、
// pageTitleを持たないページ(token-input, layout/accordion)はここで表示用ラベルを
// 補っている(該当ページ自体は変更していない)。HierarchicalMenu(サイドメニュー)・
// トップページ(リンクカード)・404ページ(リンクカラム)の3箇所から参照される共有データ。
export const MENU_TREE: MenuGroup[] = [
  {
    label: "Data",
    children: [
      { label: "チャート", href: "/data/chart" },
      { label: "データ絞り込み・並び替え", href: "/data/data-filter-sort" },
    ],
  },
  {
    label: "Form Parts",
    children: [
      { label: "カレンダー", href: "/form-parts/calendar" },
      { label: "インライン編集フィールド", href: "/form-parts/editable-text" },
      { label: "入力サジェスト", href: "/form-parts/suggest" },
      { label: "トークン入力", href: "/form-parts/token-input" },
      { label: "入力チェック", href: "/form-parts/validations" },
    ],
  },
  {
    label: "Gallery",
    children: [
      { label: "カルーセル(スライダー)", href: "/gallery/carousel" },
      { label: "ギャラリー", href: "/gallery/gallery" },
    ],
  },
  {
    label: "Layout",
    children: [
      { label: "アコーディオン", href: "/layout/accordion" },
      { label: "カラムレイアウト", href: "/layout/columns" },
      { label: "フォームレイアウト", href: "/layout/form" },
      { label: "グリッドレイアウト", href: "/layout/grid" },
      { label: "ファーストビュー", href: "/layout/hero" },
      { label: "テーブルレイアウト", href: "/layout/table" },
      { label: "タブレイアウト", href: "/layout/tabs" },
    ],
  },
  {
    label: "Others",
    children: [
      { label: "カウント", href: "/others/count" },
      { label: "認証ガード", href: "/others/protected-demo" },
      { label: "サイズ・カラーサンプル", href: "/others/size-color-sample" },
      { label: "シャッフル", href: "/others/shuffle" },
    ],
  },
  {
    label: "Optimization",
    children: [
      { label: "アルゴリズム比較(Benchmark)", href: "/optimization/benchmark" },
      { label: "経路探索(Route Planner)", href: "/optimization/route-planner" },
      { label: "ネットワーク設計(Network Designer)", href: "/optimization/network-designer" },
      { label: "シフト作成(Shift Scheduler)", href: "/optimization/shift-scheduler" },
      { label: "旅行プラン(Travel Planner)", href: "/optimization/travel-planner" },
    ],
  },
];
