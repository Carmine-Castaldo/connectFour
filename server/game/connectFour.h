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


#endif