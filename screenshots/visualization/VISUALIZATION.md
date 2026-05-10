# Data Visualization for Chess960WZ

This document provides a detailed overview of the data collected and visualized within the application. Every move is recorded into CSV files and processed using `pandas` and `matplotlib` to generate dynamic insights.
All screenshots are located in `screenshots/visualization/`.

---

## 1. Dashboard Overview
![Dashboard Overview](dashboard_overview.png)
The History and Statistics page serves as the main data hub. The left panel displays a summary statistics table containing calculated metrics such as mean, median, standard deviation, and win rates from the recorded CSV files. The right panel shows a history log of recent games, providing quick access to past results and durations.

## 2. Piece Dependency (Pie Chart)
![Piece Dependency](piece_dependency.png)
This pie chart illustrates the percentage of total moves made by each piece type. It helps players identify if they are over-relying on specific pieces (such as bringing the Queen out too early or moving Pawns excessively) during their gameplay.

## 3. Think Time by Phase (Line Chart)
![Think Time Phase](think_time.png)
This line graph tracks the average time a player spends thinking per move, categorized into three distinct game phases: Opening (moves 1-10), Middlegame (moves 11-30), and Endgame (moves 31+). It reveals time management efficiency across different stages of the match.

## 4. Capture Hesitation (Bar Chart)
![Capture Hesitation](capture_hesitation.png)
This bar chart calculates the average "think time" specifically before a player makes a capturing move, broken down by the attacking piece. It highlights psychological hesitation and tactical calculation times when initiating an attack.

## 5. Lethality Matrix (Stacked Bar Chart)
![Lethality Matrix](lethality_matrix.png)
This stacked bar chart visualizes the relationship between the attacking pieces and their targets. It shows exactly which pieces are capturing which opponent pieces most frequently, allowing players to analyze their tactical patterns and trading habits.

## 6. Overall Win Rates (Pie Chart)
![Win Rates](win_rates.png)
A straightforward pie chart summarizing the overall outcomes of all recorded games. It divides the results into White wins, Black wins, and Draws, helping determine if there is a color-side advantage bias in the player's history.

## 7. Game Duration Distribution (Histogram)
![Duration Distribution](duration_dist.png)
This histogram displays the frequency of different game durations in minutes. It provides insight into the general pacing of the matches, showing whether the games tend to be quick tactical skirmishes or long, drawn-out positional battles.

## 8. Move Count Trend (Line Chart)
![Move Count Trend](move_trend.png)
This line chart tracks the total number of half-moves per game chronologically across multiple sessions. It illustrates how the length and complexity of games evolve over time as players potentially adapt to the Chess960 format.