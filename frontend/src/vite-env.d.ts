/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the SocialScope AI backend, e.g. http://localhost:8000/api */
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
