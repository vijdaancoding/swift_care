from prompts.medical_prompt import medical_system_prompt
from prompts.crime_prompt import crime_system_prompt
from prompts.disaster_prompt import disaster_system_prompt

AGENTS = {
    "Crime": crime_system_prompt,
    "Disaster": disaster_system_prompt,
    "Medical": medical_system_prompt,
}