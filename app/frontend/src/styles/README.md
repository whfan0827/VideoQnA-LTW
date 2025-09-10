# VideoQnA Design System

## Linus Torvalds 原則應用

此設計系統遵循 Linus Torvalds 的代碼品質原則：
- **消除 Magic Numbers** - 所有數值都有語義化的變數名
- **統一 Z-index 管理** - 避免層級衝突
- **CSS Grid > 絕對定位** - 更靈活、可預測的佈局

## 設計系統結構

### 1. Spacing System (8px Grid)
```css
--spacing-unit: 8px;
--spacing-xs: 4px;   /* 0.5x */
--spacing-sm: 8px;   /* 1x */
--spacing-md: 12px;  /* 1.5x */
--spacing-lg: 16px;  /* 2x */
--spacing-xl: 24px;  /* 3x */
--spacing-2xl: 40px; /* 5x */
--spacing-3xl: 80px; /* 10x */
--spacing-4xl: 130px; /* 16.25x - 取代原來的 margin-top: 130px */
```

### 2. Z-Index Layers (統一管理)
```css
--z-base: 0;           /* 基礎層 */
--z-elevated: 10;      /* 提升內容 */
--z-sticky: 100;       /* 黏性標頭 */
--z-dropdown: 1000;    /* 下拉選單 */
--z-tooltip: 2000;     /* 工具提示 */
--z-overlay: 3000;     /* 模態框、面板 */
--z-toast: 4000;       /* 吐司通知 */
--z-debug: 9999;       /* 調試覆蓋 */
```

### 3. Layout Dimensions
```css
--header-height: 46px;
--content-max-width: 720px;
--content-padding: 24px;
--container-padding: 40px;
--command-bar-height: 48px;
--command-button-gap: 20px;
```

### 4. Colors
```css
/* 背景色 */
--color-bg-primary: #f2f2f2;     /* 主背景 */
--color-bg-secondary: #ffffff;    /* 次背景 */
--color-bg-header: #222222;       /* 標頭背景 */
--color-bg-elevated: #fafafa;     /* 提升背景 */

/* 文字顏色 */
--color-text-primary: rgba(0, 0, 0, 0.8);  /* 主文字 */
--color-text-secondary: #605e5c;            /* 次文字 */
--color-text-inverse: #f2f2f2;              /* 反色文字 */
--color-text-disabled: rgba(0, 0, 0, 0.4);  /* 禁用文字 */

/* 邊框顏色 */
--color-border-light: rgba(0, 0, 0, 0.08);  /* 淺邊框 */
--color-border-medium: #e1dfdd;             /* 中邊框 */
--color-border-strong: #c8c6c4;             /* 強邊框 */
```

### 5. Typography
```css
--font-family-base: "Segoe UI", -apple-system, ...;
--font-size-xs: 12px;
--font-size-sm: 13px;
--font-size-md: 14px;
--font-size-lg: 16px;
--font-size-xl: 18px;
--font-size-2xl: 32px;
--font-size-3xl: 40px;

--font-weight-normal: 400;
--font-weight-medium: 600;
--font-weight-bold: 700;
```

## 主要改進

### ✅ Before & After 對比

#### Magic Numbers 消除
```css
/* ❌ Before */
margin-top: 130px;
padding-left: 40px;
font-size: 16px;
z-index: 2000;

/* ✅ After */
padding-top: var(--spacing-4xl);
padding-left: var(--container-padding);
font-size: var(--font-size-lg);
z-index: var(--z-tooltip);
```

#### CSS Grid 取代絕對定位
```css
/* ❌ Before: 絕對定位 */
.commandsContainer {
    position: absolute;
    top: 0; right: 0; left: 0;
}

/* ✅ After: CSS Grid */
.oneshotMainContent {
    display: grid;
    grid-template-areas: 
        "commands"
        "content";
    grid-template-rows: var(--command-bar-height) 1fr;
}

.commandsContainer {
    grid-area: commands;
    /* 不再需要絕對定位 */
}
```

#### Z-index 統一管理
```css
/* ❌ Before: 散落各處 */
z-index: 2000; /* 在 VideoList.tsx */
z-index: 2100; /* 在另一個文件 */
z-index: 1000; /* 在第三個文件 */

/* ✅ After: 統一管理 */
z-index: var(--z-tooltip);  /* 2000 */
z-index: var(--z-overlay);  /* 3000 */
z-index: var(--z-dropdown); /* 1000 */
```

## 使用指南

### 1. 在新組件中使用
```css
.myComponent {
    padding: var(--spacing-lg);
    margin-bottom: var(--spacing-xl);
    background: var(--color-bg-secondary);
    border: 1px solid var(--color-border-light);
    font-size: var(--font-size-md);
    z-index: var(--z-elevated);
}
```

### 2. 響應式設計
```css
@media only screen and (max-width: 720px) {
    .myComponent {
        padding: var(--spacing-md);
        font-size: var(--font-size-sm);
    }
}
```

### 3. Z-index 選擇
- **--z-base** (0): 普通內容
- **--z-elevated** (10): 卡片、按鈕
- **--z-sticky** (100): 黏性標頭、導航
- **--z-dropdown** (1000): 下拉選單
- **--z-tooltip** (2000): 工具提示、彈出框
- **--z-overlay** (3000): 模態框、面板、對話框
- **--z-toast** (4000): 通知、警告
- **--z-debug** (9999): 開發調試

## 維護指南

### 新增變數
1. 在 `design-system.css` 中定義
2. 使用語義化命名
3. 遵循現有的命名約定
4. 更新此 README 文檔

### 移除 Magic Numbers
1. 搜尋硬編碼數值（如 `20px`, `#fff` 等）
2. 用對應的設計系統變數替換
3. 確保語義正確

### Z-index 衝突處理
1. 檢查 `--z-*` 變數是否合適
2. 避免直接使用數字
3. 使用 `.debug-z-index` 類調試（開發環境）

## 效益

- **✅ 一致性**: 統一的間距、顏色、字型
- **✅ 可維護性**: 修改變數即全域生效
- **✅ 可讀性**: 語義化變數名表達設計意圖
- **✅ 無衝突**: Z-index 層級管理清晰
- **✅ 響應式**: 設計系統支援各種斷點
- **✅ 效能**: CSS Grid 比絕對定位更高效

## 檔案結構
```
src/styles/
├── design-system.css  # 主設計系統文件
└── README.md         # 此文檔
```

---

**Linus 會說**: *"這就是好品味 - 通過正確的數據結構（設計系統變數）消除了特殊情況（magic numbers），讓代碼變得簡潔、一致、可預測。"*