import "@testing-library/jest-dom/vitest";

import { configure } from "@testing-library/react";
import { toHaveNoViolations } from "jest-axe";
import { afterAll, afterEach, beforeAll, expect } from "vitest";

import { server } from "./server";

expect.extend(toHaveNoViolations);

// `findBy*` waits 1s by default. Views that render from an API round trip — a
// section fed by /derive through MSW and react-query — clear that easily on an idle
// machine and miss it when vitest is running eighteen files across every core, which
// is what `make check` does. The wait is for a slow machine, not a slow assertion:
// what is being waited on still arrives in ~100ms.
//
// This must stay *below* `testTimeout` in vite.config.ts, or a query allowed to wait
// the full budget of the test containing it will never get to succeed.
configure({ asyncUtilTimeout: 5000 });

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
