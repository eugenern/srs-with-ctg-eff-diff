from dataclasses import dataclass
from numpy.linalg import lstsq # use scipy or numpy?
from numpy import dot

@dataclass
class TeamInfo:
    name: str
    pt_diff = 0
    ctg_eff_diff = 0
    gp_vs_teams: list
    
    def num_games(self) -> int:
        # WARNING: do not use this method before indices has been defined
        return -self.gp_vs_teams[indices[self.name]]

with open('game_log.txt', 'r') as results_file:
    # should we get a list of teams from API or lazily build this up as we parse game results? or iterate thru results twice to first gather teams into list?
    # probably draw from API for efficiency and intuitiveness even though it kind of creates 2 sources of truth
    teams = set()
    for result in results_file:
        teams |= set(result.split(',')[2:5:2])
    NUM_TEAMS = len(teams)
    indices = {team: index for index, team in enumerate(sorted(teams))}
    teaminfos = list(TeamInfo(team, [0] * NUM_TEAMS) for team in sorted(teams))
    sched = [teaminfo.gp_vs_teams for teaminfo in teaminfos]

    results_file.seek(0)
    for result in results_file:
        visitor, visitor_score, home, home_score = (int(x) if x.isdigit() else x for x in result.split(',')[2:6])
        v_ind, h_ind = indices[visitor], indices[home]
        v_teaminfo, h_teaminfo = teaminfos[v_ind], teaminfos[h_ind]
        
        v_teaminfo.pt_diff += visitor_score - home_score
        h_teaminfo.pt_diff += home_score - visitor_score
        
        v_teaminfo.gp_vs_teams[h_ind] += 1
        v_teaminfo.gp_vs_teams[v_ind] -= 1
        h_teaminfo.gp_vs_teams[v_ind] += 1
        h_teaminfo.gp_vs_teams[h_ind] -= 1
    
negated_pt_diffs = [-teaminfo.pt_diff for teaminfo in teaminfos]
try:
    srs_vals = lstsq(sched, negated_pt_diffs)
    if srs_vals[1].size > 0 or srs_vals[2] != NUM_TEAMS - 1:
        raise ValueError(f"Failed to properly solve linear system:\nExpected residuals to be [], got {srs_vals[1]}\nExpected rank to be {NUM_TEAMS - 1}, got {srs_vals[2]}")
except ValueError as e:
    print(e)

for teaminfo, srs in sorted(zip(teaminfos, srs_vals[0]), key=lambda x: x[1], reverse=True):
    print(teaminfo.name, f"{teaminfo.pt_diff / teaminfo.num_games():.2f}", f"{srs:.2f}")
print()

with open('league_four_factors_7_27_2025.csv', 'r') as ctg_file:
    for team_stats in ctg_file:
        team, diff = team_stats.split(',')[0:5:4]
        if team == 'Team' or team == 'Average':
            continue
        try:
            found = False
            for teaminfo in teaminfos:
                # NOTE: don't know best way to consolidate the different ways different sources name teams
                if team.split()[-1] in teaminfo.name:
                    found = True
                    teaminfo.ctg_eff_diff = float(diff)
                    break
            if found == False:
                raise ValueError(f"Could not figure out which team matches {team}.")
        except ValueError as e:
            print(e)

negated_ctg = [-teaminfo.ctg_eff_diff * teaminfo.num_games() for teaminfo in teaminfos]
try:
    srs_ctg_vals = lstsq(sched, negated_ctg)
    if srs_ctg_vals[1].size > 0 or srs_ctg_vals[2] != NUM_TEAMS - 1:
        raise ValueError(f"Failed to properly solve linear system:\nExpected residuals to be [], got {srs_ctg_vals[1]}\nExpected rank to be {NUM_TEAMS - 1}, got {srs_ctg_vals[2]}")
except ValueError as e:
    print(e)

for teaminfo, srs in sorted(zip(teaminfos, srs_ctg_vals[0]), key=lambda x: x[1], reverse=True):
    print(teaminfo.name, f"{teaminfo.ctg_eff_diff:.2f}", f"{srs:.2f}")