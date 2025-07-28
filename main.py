from dataclasses import dataclass
from numpy.linalg import lstsq # use scipy or numpy?

@dataclass
class TeamInfo:
    name: str
    pt_diff = 0
    ctg_eff_diff = 0
    gp_vs_teams: list

    def num_games(self) -> int:
        # WARNING: do not use this method before indices has been defined
        return -self.gp_vs_teams[indices[self.name]]

LINALG_ERROR_MSG = '\n'.join((
    "Failed to properly solve linear system:",
    "Expected residuals to be [], got {}",
    "Expected rank to be {}, got {}"
))

with open('game_log.csv', 'r', encoding="utf-8") as results_file:
    # how to get list of teams: from API or an extra preliminary iteration thru game results?
    # API probably makes more sense assuming it's consistent with the team names it uses
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
        raise ValueError(LINALG_ERROR_MSG.format(srs_vals[1], NUM_TEAMS - 1, srs_vals[2]))
except ValueError as e:
    # maybe in the future do more than just print the msg
    print(e)

for teaminfo, srs in sorted(zip(teaminfos, srs_vals[0]), key=lambda x: x[1], reverse=True):
    print(teaminfo.name, f"{teaminfo.pt_diff / teaminfo.num_games():.2f}", f"{srs:.2f}")
print()

with open('league_four_factors_7_27_2025.csv', 'r', encoding="utf-8") as ctg_file:
    for team_stats in ctg_file:
        team, diff = team_stats.split(',')[0:5:4]
        if team == 'Team' or team == 'Average':
            continue
        try:
            found = False
            for teaminfo in teaminfos:
                # NOTE: Will need to update name determination when using API
                if team.split()[-1] in teaminfo.name:
                    found = True
                    teaminfo.ctg_eff_diff = float(diff)
                    break
            if not found:
                raise ValueError(f"Could not figure out which team matches {team}.")
        except ValueError as e:
            # maybe in the future do more than just print the msg
            print(e)

negated_ctg = [-teaminfo.ctg_eff_diff * teaminfo.num_games() for teaminfo in teaminfos]
try:
    srs_ctg_vals = lstsq(sched, negated_ctg)
    if srs_ctg_vals[1].size > 0 or srs_ctg_vals[2] != NUM_TEAMS - 1:
        raise ValueError(LINALG_ERROR_MSG.format(srs_ctg_vals[1], NUM_TEAMS - 1, srs_ctg_vals[2]))
except ValueError as e:
    # maybe in the future do more than just print the msg
    print(e)

for teaminfo, srs in sorted(zip(teaminfos, srs_ctg_vals[0]), key=lambda x: x[1], reverse=True):
    print(teaminfo.name, f"{teaminfo.ctg_eff_diff:.2f}", f"{srs:.2f}")
