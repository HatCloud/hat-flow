# Defense-in-Depth Validation

## Overview

修复一个由无效数据引发的 bug 时，在一个地方加校验感觉就够了。但单点校验会被不同代码路径、重构或 mock 绕过。

**核心原则：** 在数据流经的每一层都校验，让这个 bug 在结构上不可能发生。

## Why Multiple Layers

单点校验只是"我们修了这个 bug"；多层校验是"我们让这个 bug 不可能发生"。

不同层捕获不同情况：

- 入口校验拦下大多数 bug。
- 业务逻辑捕获边界情况。
- 环境守卫阻止特定上下文里的危险操作。
- 调试日志在其他层都失守时帮忙定位。

## The Four Layers

### Layer 1: Entry Point Validation
**目的：** 在 API 边界拒绝明显无效的输入。

```typescript
function createProject(name: string, workingDirectory: string) {
  if (!workingDirectory || workingDirectory.trim() === '') {
    throw new Error('workingDirectory cannot be empty');
  }
  if (!existsSync(workingDirectory)) {
    throw new Error(`workingDirectory does not exist: ${workingDirectory}`);
  }
  if (!statSync(workingDirectory).isDirectory()) {
    throw new Error(`workingDirectory is not a directory: ${workingDirectory}`);
  }
  // ... proceed
}
```

### Layer 2: Business Logic Validation
**目的：** 确保数据对当前操作是合理的。

```typescript
function initializeWorkspace(projectDir: string, sessionId: string) {
  if (!projectDir) {
    throw new Error('projectDir required for workspace initialization');
  }
  // ... proceed
}
```

### Layer 3: Environment Guards
**目的：** 在特定上下文阻止危险操作。

```typescript
async function gitInit(directory: string) {
  // In tests, refuse git init outside temp directories
  if (process.env.NODE_ENV === 'test') {
    const normalized = normalize(resolve(directory));
    const tmpDir = normalize(resolve(tmpdir()));

    if (!normalized.startsWith(tmpDir)) {
      throw new Error(
        `Refusing git init outside temp dir during tests: ${directory}`
      );
    }
  }
  // ... proceed
}
```

### Layer 4: Debug Instrumentation
**目的：** 捕获上下文以备取证。

```typescript
async function gitInit(directory: string) {
  const stack = new Error().stack;
  logger.debug('About to git init', {
    directory,
    cwd: process.cwd(),
    stack,
  });
  // ... proceed
}
```

## Applying the Pattern

找到 bug 后：

1. **追踪数据流** — 坏值从哪产生？在哪被使用？
2. **标出所有检查点** — 列出数据流经的每个点。
3. **每层加校验** — 入口、业务、环境、调试。
4. **逐层测试** — 试着绕过 Layer 1，验证 Layer 2 能接住。

## Example from Session

bug：空 `projectDir` 导致 `git init` 跑进了源码目录。

**数据流：**
1. 测试 setup → 空字符串
2. `Project.create(name, '')`
3. `WorkspaceManager.createWorkspace('')`
4. `git init` 跑在 `process.cwd()`

**加的四层：**
- Layer 1: `Project.create()` 校验非空/存在/可写
- Layer 2: `WorkspaceManager` 校验 projectDir 非空
- Layer 3: `WorktreeManager` 在测试中拒绝 tmpdir 之外的 git init
- Layer 4: git init 前记录 stack trace

## Key Insight

四层缺一不可。测试期间，每一层都接住了其他层漏掉的 bug：

- 不同代码路径绕过了入口校验。
- mock 绕过了业务逻辑检查。
- 不同平台的边界情况需要环境守卫。
- 调试日志识别出结构性误用。

校验止于单点是不够的，在每一层都加检查。
