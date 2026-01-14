// Dynamically build the configuration based on environment variables
const config = {
  //dryRun: 'full',
  platform: process.env.RENOVATE_PLATFORM,
  
  // Authentication and Identity
  username: process.env.RENOVATE_USERNAME,
  gitAuthor: process.env.RENOVATE_GIT_AUTHOR,
  
  // Discovery
  autodiscover: true,
  
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

// Ensure autodiscoverFilter is always an array if provided
if (process.env.RENOVATE_AUTODISCOVER_FILTER && process.env.RENOVATE_AUTODISCOVER_FILTER.trim() !== "") {
  config.autodiscoverFilter = process.env.RENOVATE_AUTODISCOVER_FILTER.split(',').map(s => s.trim());
}

module.exports = config;
