/* eslint-disable */
/* tslint:disable */
// @ts-nocheck
/*
 * ---------------------------------------------------------------
 * ## THIS FILE WAS GENERATED VIA SWAGGER-TYPESCRIPT-API        ##
 * ##                                                           ##
 * ## AUTHOR: acacode                                           ##
 * ## SOURCE: https://github.com/acacode/swagger-typescript-api ##
 * ---------------------------------------------------------------
 */

/** ActivityPage */
export interface ActivityPage {
  /**
   * Items
   * @maxItems 50
   */
  items: (
    | ({
        kind: "batch";
      } & BatchActivity)
    | ({
        kind: "feedback";
      } & FeedbackActivity)
  )[];
  /** Next Cursor */
  next_cursor: string | null;
  /**
   * Refresh Cursor
   * Rehydrate the first page of this same frozen view
   */
  refresh_cursor: string;
  /**
   * Total
   * Items in this frozen read window
   * @min 0
   * @max 6000
   */
  total: number;
  /**
   * Has Older
   * Older stored activity exists beyond the latest 6000-item window
   */
  has_older: boolean;
  /** Revision */
  revision: number;
}

/** AnalysisInput */
export interface AnalysisInput {
  /**
   * Identity
   * Unique submission identity retained across retries
   * @minLength 1
   * @maxLength 100
   */
  identity: string;
}

/** BackfillCreated */
export interface BackfillCreated {
  /**
   * Id
   * Identifier of the persisted fixed-selection backfill
   */
  id: string;
}

/** BackfillInput */
export interface BackfillInput {
  /**
   * Record Ids
   * @maxItems 100
   * @minItems 1
   */
  record_ids: string[];
  /**
   * Config
   * @default "v2"
   */
  config?: "v1" | "v2";
}

/** BatchActivity */
export interface BatchActivity {
  /**
   * Kind
   * @default "batch"
   */
  kind?: "batch";
  /** Id */
  id: string;
  batch: BatchView;
}

/** BatchItem */
export interface BatchItem {
  /** Record Id */
  record_id: string;
  /** Sequence */
  sequence: number;
  /** Text */
  text: string;
  /** Channel */
  channel: string;
  /** Original target-configuration job; later individual analyses are excluded */
  job: JobView | null;
  /** Completed output of that exact job run, or null if none was stored */
  output: OutputView | null;
}

/** BatchPage */
export interface BatchPage {
  batch: BatchView;
  /**
   * Items
   * @maxItems 50
   */
  items: BatchItem[];
  /**
   * Next Cursor
   * Signed continuation for this workspace/batch, or null at the end
   */
  next_cursor: string | null;
}

/** BatchView */
export interface BatchView {
  /** Id */
  id: string;
  /** Config */
  config: "v1" | "v2";
  /** Selected */
  selected: number;
  /** Completed */
  completed: number;
  /** Failed */
  failed: number;
  /** Cancelled */
  cancelled: boolean;
  /** Watermark */
  watermark: number;
}

/** Credentials */
export interface Credentials {
  /**
   * Email
   * @minLength 3
   * @maxLength 254
   * @pattern ^[^\s@]+@[^\s@]+\.[^\s@]+$
   */
  email: string;
  /**
   * Password
   * 12–128 character password; hashed with Argon2id
   * @minLength 12
   * @maxLength 128
   */
  password: string;
}

/**
 * EmptyRequest
 * An explicit empty JSON request body.
 */
export type EmptyRequest = object;

/** ErrorResponse */
export interface ErrorResponse {
  /**
   * Detail
   * Safe explanation; never includes credentials or provider bodies
   */
  detail: string;
}

/** FeedPage */
export interface FeedPage {
  /** Workspace Id */
  workspace_id: string;
  /** Records */
  records: RecordView[];
  /**
   * Next Cursor
   * Opaque continuation token, or null when this frozen view is exhausted
   */
  next_cursor: string | null;
  /**
   * Refresh Cursor
   * Refresh the first page of this same frozen view without changing membership
   */
  refresh_cursor: string;
  /**
   * Watermark
   * Highest source sequence when this view opened
   */
  watermark: number;
  /** Revision */
  revision: number;
  /**
   * Total
   * Number of records matching the frozen view
   */
  total: number;
}

/** FeedStatus */
export interface FeedStatus {
  /** Workspace Id */
  workspace_id: string;
  /** Revision */
  revision: number;
  /** Latest Sequence */
  latest_sequence: number;
  /** Received */
  received: number;
  /** Enriched */
  enriched: number;
  /** Failed */
  failed: number;
  /** Batches */
  batches: BatchView[];
  /** Provider */
  provider: string;
}

/** FeedbackActivity */
export interface FeedbackActivity {
  /**
   * Kind
   * @default "feedback"
   */
  kind?: "feedback";
  /** Id */
  id: string;
  feedback: BatchItem;
}

/** FeedbackInput */
export interface FeedbackInput {
  /**
   * Identity
   * @minLength 1
   * @maxLength 100
   */
  identity: string;
  /**
   * Text
   * @minLength 1
   * @maxLength 4000
   */
  text: string;
  /** Channel */
  channel: "Support" | "In-app" | "Community";
}

/** HTTPValidationError */
export interface HTTPValidationError {
  /** Detail */
  detail?: ValidationError[];
}

/** HealthResponse */
export interface HealthResponse {
  /**
   * Status
   * @default "ok"
   */
  status?: "ok";
  /**
   * Provider
   * Configured provider identifier, not a secret
   */
  provider: string;
}

/** Identity */
export interface Identity {
  /** Workspace Id */
  workspace_id: string;
  /** Email */
  email: string | null;
  /** Kind */
  kind: "account" | "demo";
}

/** JobView */
export interface JobView {
  /** Id */
  id: string;
  /** Config */
  config: "v1" | "v2";
  /**
   * Run
   * Monotonic analysis revision within this feedback
   * @min 1
   */
  run: number;
  /** Provider */
  provider: string;
  /** Status */
  status: "queued" | "leased" | "succeeded" | "failed" | "cancelled";
  /** Attempts */
  attempts: number;
  /** Error */
  error: string | null;
  /** Origin */
  origin: "live" | "backfill" | "analysis";
}

/** OkResponse */
export interface OkResponse {
  /**
   * Ok
   * @default true
   */
  ok?: boolean;
}

/** OutputView */
export interface OutputView {
  /** Topic */
  topic: "reliability" | "usability" | "billing" | "performance" | "other";
  /** Intent */
  intent: "issue" | "request" | "praise" | "unclear";
  /**
   * Summary
   * @minLength 1
   * @maxLength 240
   */
  summary: string;
  /**
   * Evidence
   * @maxItems 3
   * @minItems 1
   */
  evidence: string[];
  /** Config */
  config: "v1" | "v2";
  /**
   * Run
   * The completed job revision; previous outputs are retained
   * @min 1
   */
  run: number;
  /** Provider */
  provider: string;
  /** Created At */
  created_at: string;
}

/** RecordView */
export interface RecordView {
  /** Id */
  id: string;
  /** Sequence */
  sequence: number;
  /** Text */
  text: string;
  /** Channel */
  channel: string;
  /** Ingested At */
  ingested_at: string;
  /**
   * Jobs
   * The latest ten jobs, ordered by increasing run
   * @maxItems 10
   */
  jobs: JobView[];
  /**
   * Outputs
   * The latest ten successful outputs, ordered by increasing run
   * @maxItems 10
   */
  outputs: OutputView[];
}

/** SessionResult */
export interface SessionResult {
  /** Workspace Id */
  workspace_id: string;
  /** Email */
  email: string | null;
  /** Kind */
  kind: "account" | "demo";
  /**
   * Token
   * Opaque bearer token, valid for 24 hours; stored hashed by the server
   */
  token: string;
}

/** SimulationCreated */
export interface SimulationCreated {
  /**
   * Inserted
   * Number of newly inserted immutable records
   * @min 0
   * @max 12
   */
  inserted: number;
}

/** SimulationInput */
export interface SimulationInput {
  /**
   * Request Id
   * @pattern ^[a-zA-Z0-9-]{1,64}$
   */
  request_id: string;
  /**
   * Count
   * @min 1
   * @max 12
   * @default 12
   */
  count?: number;
}

/** ValidationError */
export interface ValidationError {
  /** Location */
  loc: (string | number)[];
  /** Message */
  msg: string;
  /** Error Type */
  type: string;
  /** Input */
  input?: any;
  /** Context */
  ctx?: object;
}

/**  Body */
export type CreateDemoSessionPayload = EmptyRequest | null;

export type CreateDemoSessionData = SessionResult;

export type RegisterAccountData = SessionResult;

export type LoginAccountData = SessionResult;

export type GetCurrentIdentityData = Identity;

/**  Body */
export type LogoutSessionPayload = EmptyRequest | null;

export type LogoutSessionData = OkResponse;

export interface ListFeedbackParams {
  /**
   * Q
   * Case-insensitive source-text substring; retained with the cursor
   * @maxLength 100
   * @default ""
   */
  q?: string;
  /**
   * Status
   * Latest configuration's job status at view creation
   * @default "all"
   */
  status?: "all" | "queued" | "leased" | "succeeded" | "failed" | "cancelled";
  /**
   * Topic
   * Latest stored output topic at view creation
   * @default "all"
   */
  topic?:
    "all" | "reliability" | "usability" | "billing" | "performance" | "other";
  /**
   * Limit
   * Page size; default UI page is twelve
   * @min 1
   * @max 50
   * @default 12
   */
  limit?: number;
  /**
   * Cursor
   * Opaque next_cursor or refresh_cursor from the same workspace/filter view; absent opens a current view. Invalid values return 400; retained expired views return 410.
   */
  cursor?: string | null;
}

export type ListFeedbackData = FeedPage;

export type CreateFeedbackData = RecordView;

export type GetFeedbackStatusData = FeedStatus;

export type CreateSimulationData = SimulationCreated;

export interface GetFeedbackParams {
  /** Record Id */
  recordId: string;
}

export type GetFeedbackData = RecordView;

export interface AnalyzeFeedbackParams {
  /** Record Id */
  recordId: string;
}

export type AnalyzeFeedbackData = RecordView;

export interface ListActivityParams {
  /**
   * Limit
   * Maximum items per page; default ten
   * @min 1
   * @max 50
   * @default 10
   */
  limit?: number;
  /**
   * Cursor
   * Opaque next_cursor or refresh_cursor from this activity view
   */
  cursor?: string | null;
}

export type ListActivityData = ActivityPage;

export interface GetBackfillParams {
  /**
   * Limit
   * Maximum items per page; default ten
   * @min 1
   * @max 50
   * @default 10
   */
  limit?: number;
  /**
   * Cursor
   * Opaque next_cursor for this workspace/batch; omit to read its first page
   */
  cursor?: string | null;
  /**
   * Batch Id
   * Persisted fixed-selection backfill identifier
   */
  batchId: string;
}

export type GetBackfillData = BatchPage;

export type CreateBackfillData = BackfillCreated;

/**  Body */
export type CancelBackfillPayload = EmptyRequest | null;

export interface CancelBackfillParams {
  /**
   * Batch Id
   * Backfill id returned by createBackfill
   */
  batchId: string;
}

export type CancelBackfillData = OkResponse;

/**  Body */
export type RetryEnrichmentPayload = EmptyRequest | null;

export interface RetryEnrichmentParams {
  /**
   * Job Id
   * Job id from a feedback record's processing history
   */
  jobId: string;
}

export type RetryEnrichmentData = OkResponse;

export type GetHealthData = HealthResponse;

export type QueryParamsType = Record<string | number, any>;
export type ResponseFormat = keyof Omit<Body, "body" | "bodyUsed">;

export interface FullRequestParams extends Omit<RequestInit, "body"> {
  /** set parameter to `true` for call `securityWorker` for this request */
  secure?: boolean;
  /** request path */
  path: string;
  /** content type of request body */
  type?: ContentType;
  /** query params */
  query?: QueryParamsType;
  /** format of response (i.e. response.json() -> format: "json") */
  format?: ResponseFormat;
  /** request body */
  body?: unknown;
  /** base url */
  baseUrl?: string;
  /** request cancellation token */
  cancelToken?: CancelToken;
}

export type RequestParams = Omit<
  FullRequestParams,
  "body" | "method" | "query" | "path"
>;

export interface ApiConfig<SecurityDataType = unknown> {
  baseUrl?: string;
  baseApiParams?: Omit<RequestParams, "baseUrl" | "cancelToken" | "signal">;
  securityWorker?: (
    securityData: SecurityDataType | null
  ) => Promise<RequestParams | void> | RequestParams | void;
  customFetch?: typeof fetch;
}

export interface HttpResponse<
  D extends unknown,
  E extends unknown = unknown,
> extends Response {
  data: D;
  error: E;
}

type CancelToken = Symbol | string | number;

export enum ContentType {
  Json = "application/json",
  JsonApi = "application/vnd.api+json",
  FormData = "multipart/form-data",
  UrlEncoded = "application/x-www-form-urlencoded",
  Text = "text/plain",
}

export class HttpClient<SecurityDataType = unknown> {
  public baseUrl: string = "";
  private securityData: SecurityDataType | null = null;
  private securityWorker?: ApiConfig<SecurityDataType>["securityWorker"];
  private abortControllers = new Map<CancelToken, AbortController>();
  private customFetch = (...fetchParams: Parameters<typeof fetch>) =>
    fetch(...fetchParams);

  private baseApiParams: RequestParams = {
    credentials: "same-origin",
    headers: {},
    redirect: "follow",
    referrerPolicy: "no-referrer",
  };

  constructor(apiConfig: ApiConfig<SecurityDataType> = {}) {
    Object.assign(this, apiConfig);
  }

  public setSecurityData = (data: SecurityDataType | null) => {
    this.securityData = data;
  };

  protected encodeQueryParam(key: string, value: any) {
    const encodedKey = encodeURIComponent(key);
    return `${encodedKey}=${encodeURIComponent(typeof value === "number" ? value : `${value}`)}`;
  }

  protected addQueryParam(query: QueryParamsType, key: string) {
    return this.encodeQueryParam(key, query[key]);
  }

  protected addArrayQueryParam(query: QueryParamsType, key: string) {
    const value = query[key];
    return value.map((v: any) => this.encodeQueryParam(key, v)).join("&");
  }

  protected toQueryString(rawQuery?: QueryParamsType): string {
    const query = rawQuery || {};
    const keys = Object.keys(query).filter(
      key => "undefined" !== typeof query[key]
    );
    return keys
      .map(key =>
        Array.isArray(query[key])
          ? this.addArrayQueryParam(query, key)
          : this.addQueryParam(query, key)
      )
      .join("&");
  }

  protected addQueryParams(rawQuery?: QueryParamsType): string {
    const queryString = this.toQueryString(rawQuery);
    return queryString ? `?${queryString}` : "";
  }

  private contentFormatters: Record<ContentType, (input: any) => any> = {
    [ContentType.Json]: (input: any) =>
      input !== null && (typeof input === "object" || typeof input === "string")
        ? JSON.stringify(input)
        : input,
    [ContentType.JsonApi]: (input: any) =>
      input !== null && (typeof input === "object" || typeof input === "string")
        ? JSON.stringify(input)
        : input,
    [ContentType.Text]: (input: any) =>
      input !== null && typeof input !== "string"
        ? JSON.stringify(input)
        : input,
    [ContentType.FormData]: (input: any) => {
      if (input instanceof FormData) {
        return input;
      }

      return Object.keys(input || {}).reduce((formData, key) => {
        const property = input[key];
        formData.append(
          key,
          property instanceof Blob
            ? property
            : typeof property === "object" && property !== null
              ? JSON.stringify(property)
              : `${property}`
        );
        return formData;
      }, new FormData());
    },
    [ContentType.UrlEncoded]: (input: any) => this.toQueryString(input),
  };

  protected mergeRequestParams(
    params1: RequestParams,
    params2?: RequestParams
  ): RequestParams {
    return {
      ...this.baseApiParams,
      ...params1,
      ...(params2 || {}),
      headers: {
        ...(this.baseApiParams.headers || {}),
        ...(params1.headers || {}),
        ...((params2 && params2.headers) || {}),
      },
    };
  }

  protected createAbortSignal = (
    cancelToken: CancelToken
  ): AbortSignal | undefined => {
    if (this.abortControllers.has(cancelToken)) {
      const abortController = this.abortControllers.get(cancelToken);
      if (abortController) {
        return abortController.signal;
      }
      return void 0;
    }

    const abortController = new AbortController();
    this.abortControllers.set(cancelToken, abortController);
    return abortController.signal;
  };

  public abortRequest = (cancelToken: CancelToken) => {
    const abortController = this.abortControllers.get(cancelToken);

    if (abortController) {
      abortController.abort();
      this.abortControllers.delete(cancelToken);
    }
  };

  public request = async <T = any, E = any>({
    body,
    secure,
    path,
    type,
    query,
    format,
    baseUrl,
    cancelToken,
    ...params
  }: FullRequestParams): Promise<HttpResponse<T, E>> => {
    const secureParams =
      ((typeof secure === "boolean" ? secure : this.baseApiParams.secure) &&
        this.securityWorker &&
        (await this.securityWorker(this.securityData))) ||
      {};
    const requestParams = this.mergeRequestParams(params, secureParams);
    const queryString = query && this.toQueryString(query);
    const payloadFormatter = this.contentFormatters[type || ContentType.Json];
    const responseFormat = format || requestParams.format;

    return this.customFetch(
      `${baseUrl || this.baseUrl || ""}${path}${queryString ? `?${queryString}` : ""}`,
      {
        ...requestParams,
        headers: {
          ...(requestParams.headers || {}),
          ...(type && type !== ContentType.FormData
            ? { "Content-Type": type }
            : {}),
        },
        signal:
          (cancelToken
            ? this.createAbortSignal(cancelToken)
            : requestParams.signal) || null,
        body:
          typeof body === "undefined" || body === null
            ? null
            : payloadFormatter(body),
      }
    ).then(async response => {
      const r = response as HttpResponse<T, E>;
      r.data = null as unknown as T;
      r.error = null as unknown as E;

      const responseToParse = responseFormat ? response.clone() : response;
      const data = !responseFormat
        ? r
        : await responseToParse[responseFormat]()
            .then(data => {
              if (r.ok) {
                r.data = data;
              } else {
                r.error = data;
              }
              return r;
            })
            .catch(e => {
              r.error = e;
              return r;
            });

      if (cancelToken) {
        this.abortControllers.delete(cancelToken);
      }

      if (!response.ok) throw data;
      return data;
    });
  };
}

/**
 * @title Feedback Desk API
 * @version 0.3.0
 *
 * Independent customer-feedback workspace API. First register, sign in or open a demo; use its returned token in Authorize (WorkspaceBearer). Protected reads and writes are scoped to that workspace. Immutable input and versioned results are processed by a separate durable worker. No worker/provider credentials are exposed by this API.
 */
export class Api<
  SecurityDataType extends unknown,
> extends HttpClient<SecurityDataType> {
  api = {
    /**
     * @description Creates a temporary workspace and a revocable 24-hour bearer token. Seeds 24 synthetic records with deterministic jobs, even when live provider tests are configured. Limited to 20 auth requests per IP per 15 minutes. Send an empty JSON object.
     *
     * @tags Authentication
     * @name CreateDemoSession
     * @summary Open an isolated synthetic demo
     * @request POST:/api/auth/demo
     */
    createDemoSession: (
      data: CreateDemoSessionPayload,
      params: RequestParams = {}
    ) =>
      this.request<CreateDemoSessionData, ErrorResponse | HTTPValidationError>({
        path: `/api/auth/demo`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description Creates an empty personal workspace. Passwords are hashed with Argon2id; they are never returned. Email is normalized to lowercase. No email verification or password reset is implemented. Limited by both IP and email.
     *
     * @tags Authentication
     * @name RegisterAccount
     * @summary Create an independent personal account
     * @request POST:/api/auth/register
     */
    registerAccount: (data: Credentials, params: RequestParams = {}) =>
      this.request<RegisterAccountData, ErrorResponse | HTTPValidationError>({
        path: `/api/auth/register`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description Returns a new opaque token for the existing workspace without deleting its records. Tokens expire after 24 hours; at most ten active sessions per account. Invalid credentials use a generic error. Email admission allows ten attempts per 15 minutes; IP admission allows twenty.
     *
     * @tags Authentication
     * @name LoginAccount
     * @summary Sign in to an existing account
     * @request POST:/api/auth/login
     */
    loginAccount: (data: Credentials, params: RequestParams = {}) =>
      this.request<LoginAccountData, ErrorResponse | HTTPValidationError>({
        path: `/api/auth/login`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description Validates the bearer token and returns only its workspace and account/demo identity.
     *
     * @tags Authentication
     * @name GetCurrentIdentity
     * @summary Read the current session identity
     * @request GET:/api/auth/me
     * @secure
     */
    getCurrentIdentity: (params: RequestParams = {}) =>
      this.request<GetCurrentIdentityData, ErrorResponse>({
        path: `/api/auth/me`,
        method: "GET",
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * @description Revokes this token immediately. Other account sessions remain valid. The UI separately clears its private query and offline caches. Send an empty JSON object.
     *
     * @tags Authentication
     * @name LogoutSession
     * @summary Revoke the current bearer token
     * @request POST:/api/auth/logout
     * @secure
     */
    logoutSession: (data: LogoutSessionPayload, params: RequestParams = {}) =>
      this.request<LogoutSessionData, ErrorResponse | HTTPValidationError>({
        path: `/api/auth/logout`,
        method: "POST",
        body: data,
        secure: true,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description The first request freezes matching IDs for ten minutes (at most twenty views per workspace). Subsequent requests use a signed opaque cursor and descending sequence keyset with SQL LIMIT. Only one page is hydrated. Processing results may refresh, but membership stays fixed to prevent skips/duplicates. New arrivals and changed matches appear after starting without a cursor. Never construct or reuse a cursor with another workspace or filter.
     *
     * @tags Feedback
     * @name ListFeedback
     * @summary Read one stable page of feedback
     * @request GET:/api/feedback
     * @secure
     */
    listFeedback: (query: ListFeedbackParams, params: RequestParams = {}) =>
      this.request<ListFeedbackData, ErrorResponse | HTTPValidationError>({
        path: `/api/feedback`,
        method: "GET",
        query: query,
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * @description Accepts user-authored text and an allowed channel. Retain a unique identity for this submission across network retries: identical identity/text/channel returns the existing record with 200; changed content under that identity returns 409. A new immutable input and its durable job commit together and return 201. The separate worker processes it using the configured provider; the request does not wait for enrichment. Existing per-workspace and global limits apply.
     *
     * @tags Feedback
     * @name CreateFeedback
     * @summary Submit a feedback message for processing
     * @request POST:/api/feedback
     * @secure
     */
    createFeedback: (data: FeedbackInput, params: RequestParams = {}) =>
      this.request<CreateFeedbackData, ErrorResponse | HTTPValidationError>({
        path: `/api/feedback`,
        method: "POST",
        body: data,
        secure: true,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description Returns workspace totals and at most ten backfills. latest_sequence can signal arrivals newer than the current feed watermark. The UI polls every three seconds; this endpoint does not stream events.
     *
     * @tags Feedback
     * @name GetFeedbackStatus
     * @summary Read counts, processing progress and new-arrival marker
     * @request GET:/api/status
     * @secure
     */
    getFeedbackStatus: (params: RequestParams = {}) =>
      this.request<GetFeedbackStatusData, ErrorResponse>({
        path: `/api/status`,
        method: "GET",
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * @description Commits one to twelve immutable inputs and durable v1 jobs atomically. Repeating request_id is idempotent; conflicting content is rejected. Bounds: 500 records per workspace and 5,000 globally. A separate worker processes jobs; the HTTP request does not wait for enrichment.
     *
     * @tags Feedback
     * @name CreateSimulation
     * @summary Enqueue a finite batch of synthetic feedback
     * @request POST:/api/simulations
     * @secure
     */
    createSimulation: (data: SimulationInput, params: RequestParams = {}) =>
      this.request<CreateSimulationData, ErrorResponse | HTTPValidationError>({
        path: `/api/simulations`,
        method: "POST",
        body: data,
        secure: true,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description Opens a feedback record directly, independently of the current list or cursor. Only a record belonging to the authenticated workspace can be read. Missing and foreign-workspace IDs both return 404. Includes immutable source, jobs and all completed result versions.
     *
     * @tags Feedback
     * @name GetFeedback
     * @summary Read one feedback message and its processing history
     * @request GET:/api/feedback/{record_id}
     * @secure
     */
    getFeedback: (
      { recordId, ...query }: GetFeedbackParams,
      params: RequestParams = {}
    ) =>
      this.request<GetFeedbackData, ErrorResponse | HTTPValidationError>({
        path: `/api/feedback/${recordId}`,
        method: "GET",
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * @description Creates a new durable analysis run using the configured real provider. Previous results remain visible while it runs. Retain identity for network retries: a replay returns 200 without another run; a new request returns 202. One active run per feedback; concurrent requests return 409. There is no lifetime run limit. Record responses include the latest ten jobs and successful outputs. Missing or foreign records return 404. Real-provider mode and calls must be enabled, otherwise 503. Provider budgets, timeouts, output validation and three-attempt limit still apply; acceptance does not guarantee provider availability or successful completion.
     *
     * @tags Feedback
     * @name AnalyzeFeedback
     * @summary Request a new AI analysis of one feedback message
     * @request POST:/api/feedback/{record_id}/analysis
     * @secure
     */
    analyzeFeedback: (
      { recordId, ...query }: AnalyzeFeedbackParams,
      data: AnalysisInput,
      params: RequestParams = {}
    ) =>
      this.request<AnalyzeFeedbackData, ErrorResponse | HTTPValidationError>({
        path: `/api/feedback/${recordId}/analysis`,
        method: "POST",
        body: data,
        secure: true,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description Includes one item per automatic or individual analysis job, and one per bulk backfill (without duplicate child-job items). Each job shows only its exact stored output revision. A new view orders IDs by current scheduling availability and an ID tie-breaker; this is not a creation timestamp. Membership and order freeze for ten minutes; status/results can refresh through refresh_cursor. Signed workspace-scoped cursors page persisted positions with SQL LIMIT. At most twenty views are retained per workspace, shared with feedback/backfill views. Each read window contains at most the latest 6000 IDs; has_older reports older stored activity without blocking new work or deleting history. This flag stays fixed throughout the view. Omit cursor to include new work. This endpoint never enqueues work or calls a provider.
     *
     * @tags Activity
     * @name ListActivity
     * @summary Read automatic, individual and bulk analysis activity
     * @request GET:/api/activity
     * @secure
     */
    listActivity: (query: ListActivityParams, params: RequestParams = {}) =>
      this.request<ListActivityData, ErrorResponse | HTTPValidationError>({
        path: `/api/activity`,
        method: "GET",
        query: query,
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * @description Pages the persisted fixed selection in descending source sequence with SQL keyset pagination. Membership never expands with new arrivals. Each item shows its original non-analysis target-configuration job and only that job's output; later individual analyses are excluded. A selection may reuse an already completed target version. Progress and job states may refresh. Missing and foreign-workspace batches both return 404. Signed cursors are bound to this workspace and batch for ten minutes, sharing the twenty-view workspace limit with feedback views. Reading does not enqueue work or call a provider.
     *
     * @tags Backfills and recovery
     * @name GetBackfill
     * @summary Read the feedback and original results of one backfill
     * @request GET:/api/backfills/{batch_id}
     * @secure
     */
    getBackfill: (
      { batchId, ...query }: GetBackfillParams,
      params: RequestParams = {}
    ) =>
      this.request<GetBackfillData, ErrorResponse | HTTPValidationError>({
        path: `/api/backfills/${batchId}`,
        method: "GET",
        query: query,
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * @description Freezes up to 100 record IDs belonging to this workspace and enqueues the missing target versions atomically. Input and previous outputs stay unchanged. The unique (record, config) operation is idempotent; existing unfinished work must be retried or cancelled, not duplicated. Progress is available in /api/status.
     *
     * @tags Backfills and recovery
     * @name CreateBackfill
     * @summary Reprocess a fixed selection with another configuration
     * @request POST:/api/backfills
     * @secure
     */
    createBackfill: (data: BackfillInput, params: RequestParams = {}) =>
      this.request<CreateBackfillData, ErrorResponse | HTTPValidationError>({
        path: `/api/backfills`,
        method: "POST",
        body: data,
        secure: true,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description Cancels queued/claimed jobs and fences in-flight completions. Already completed versions are preserved. Only a batch in the current workspace can be cancelled. Send an empty JSON object.
     *
     * @tags Backfills and recovery
     * @name CancelBackfill
     * @summary Stop unfinished work in a backfill
     * @request POST:/api/backfills/{batch_id}/cancel
     * @secure
     */
    cancelBackfill: (
      { batchId, ...query }: CancelBackfillParams,
      data: CancelBackfillPayload,
      params: RequestParams = {}
    ) =>
      this.request<CancelBackfillData, ErrorResponse | HTTPValidationError>({
        path: `/api/backfills/${batchId}/cancel`,
        method: "POST",
        body: data,
        secure: true,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * @description Only terminal jobs in this workspace with fewer than three lifetime attempts can be retried. Retry retains the original provider/configuration and does not overwrite completed output. Failed provider calls never silently switch to deterministic mode. Send an empty JSON object.
     *
     * @tags Backfills and recovery
     * @name RetryEnrichment
     * @summary Retry an eligible failed or cancelled version
     * @request POST:/api/jobs/{job_id}/retry
     * @secure
     */
    retryEnrichment: (
      { jobId, ...query }: RetryEnrichmentParams,
      data: RetryEnrichmentPayload,
      params: RequestParams = {}
    ) =>
      this.request<RetryEnrichmentData, ErrorResponse | HTTPValidationError>({
        path: `/api/jobs/${jobId}/retry`,
        method: "POST",
        body: data,
        secure: true,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),
  };
  health = {
    /**
     * @description Checks a PostgreSQL connection. It does not prove worker progress or model-provider availability. No credentials or worker internals are returned.
     *
     * @tags Health
     * @name GetHealth
     * @summary Check API/database readiness
     * @request GET:/health
     */
    getHealth: (params: RequestParams = {}) =>
      this.request<GetHealthData, any>({
        path: `/health`,
        method: "GET",
        format: "json",
        ...params,
      }),
  };
}
