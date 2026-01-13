module.exports = {
  // Platform configuration
  platform: process.env.RENOVATE_PLATFORM,
  endpoint: process.env.RENOVATE_ENDPOINT || undefined,
  
  // Authentication and Identity
  username: process.env.RENOVATE_USERNAME,
  gitAuthor: process.env.RENOVATE_GIT_AUTHOR,
  
  // Discovery
  autodiscover: true,
  autodiscoverFilter: process.env.RENOVATE_AUTODISCOVER_FILTER,
  
  // General behavior
  onboarding: true,
  optimizeForDisabled: false,
  repositoryCache: 'enabled',

  // Security: Prevent execution of arbitrary commands
  allowedCommands: [],
  allowedUnsafeExecutions: [],
  ignoreScripts: true,
  exposeAllEnv: false, // Explicitly prevent child processes from accessing secrets
  executionTimeout: 15, // Prevent a single repo from stalling the bot (15 mins)
  
  // Add any other global configuration here
  // Useful if you plan to make this private, not recommended for public apps
  // packageRules: [ ... ],
};
