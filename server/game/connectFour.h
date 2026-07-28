#ifndef CONNECTFOUR_H
#define CONNECTFOUR_H

#define rows 6
#define colums 7

typedef struct{

    int id_match, state;
    int * player1, * player2;
    int fd_giocatore1, fd_giocatore2;
    int turn, moves;
    int grid[7][6];

} Match;

void init_match(Match * match);
int insertDisc(Match * match,int colum, int id_player);
int is_colum_empty(Match * match, int colum);
int get_empy_row(Match * match, int colum);
int check_draw(Match * match);
int check_win(Match * match, int last_move_colum);
int check_win_colum(Match * match, int last_move_colum, int last_row, int disc_player);
int check_win_row(Match * match, int last_move_colum, int last_row, int disc_player);
int check_win_main_diagonal(Match * match, int last_move_colum, int last_row, int disc_player);
int check_win_sec_diagonal(Match * match, int last_move_colum, int last_row, int disc_player);
#endif