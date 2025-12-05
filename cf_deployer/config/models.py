from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class StackConfig:
    name: str
    template: str
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TeamConfig:
    name: str
    stacks: List[StackConfig] = field(default_factory=list)

@dataclass
class EnvironmentConfig:
    aws_profile: str
    region: str
    teams: Dict[str, TeamConfig] = field(default_factory=dict)
