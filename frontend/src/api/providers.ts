const sampleProviders = new Set([
  "deterministic-rules/1",
  "deterministic/fixture",
  "browser-fixture/1",
]);

const aiProviders = new Map([["openrouter", "OpenRouter"]]);

const identifyAiProvider = (provider: string | undefined) => {
  if (!provider) return undefined;

  const separator = provider.indexOf("/");

  if (separator < 1) return undefined;

  const name = aiProviders.get(provider.slice(0, separator));
  const model = provider.slice(separator + 1);

  if (!name || model.split("/").some(part => !part || part !== part.trim()))
    return undefined;

  return { name, model };
};

export const isSampleProvider = (provider: string | undefined): boolean =>
  !!provider && sampleProviders.has(provider);

export const isAiProvider = (provider: string | undefined): boolean =>
  !!identifyAiProvider(provider);

export const formatProvider = (provider: string | undefined): string => {
  if (isSampleProvider(provider)) return "Sample analysis";

  const ai = identifyAiProvider(provider);

  if (ai) return `AI · ${ai.model} · ${ai.name}`;

  return provider?.trim()
    ? `Provider · ${provider}`
    : "Provider not identified";
};
