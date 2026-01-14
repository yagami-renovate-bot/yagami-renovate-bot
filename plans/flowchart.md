``` mermaid
graph TD
    A[Start] --> B{Run get_installations.py};
    B --> C{For each installation};
    C --> D{RENOVATE_HASH_ALL_NAMESPACES is true?};
    D -- Yes --> E[Set Namespace to SHA1 of owner];
    D -- No --> F{account.user_view_type is private?};
    F -- Yes --> E;
    F -- No --> G[Set Namespace to original owner];
    E --> H[Add resulting namespace to matrix];
    G --> H;
    H --> I{All installations processed?};
    I -- No --> C;
    I -- Yes --> J[Generate JSON matrix];
    J --> K[Start Renovate jobs];
    K --> L[Use matrix.owner in job name];
    L --> M[End];
```
