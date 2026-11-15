import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { AppRouter } from "@/router";

const queryClient = new QueryClient();

export const App = () => (
  <QueryClientProvider client={queryClient}>
    <AppRouter />
  </QueryClientProvider>
);
