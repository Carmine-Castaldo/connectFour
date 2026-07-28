#include <stdio.h>
#include "connectFour.h"

    
void init_match(Match * match){
    match->moves = 0;
    for(int i = 0; i < rows; i++)
        for(int j = 0; j < colums ; j++)
            match->grid[i][j] = 0;
}

int insertDisc(Match * match,int colum, int id_player){
    int row = get_empy_row(match, colum);
    if( row != -1){
        match->grid[row][colum] = id_player;
        match->moves++;
        return 1;
    }
    else
        printf("ERROR: Illegal Move\n"); 

    return 0;
    
}

int is_colum_empty(Match * match, int colum){
    return (match->grid[0][colum] == 0);
}

int get_empy_row(Match * match, int colum){
    for(int i = rows-1; i >= 0; i--)
        if( match->grid[i][colum] == 0)
             return i;
    
    return -1;
}


int check_draw(Match * match){
    if(match->moves == rows * colums) return 1;
    else return 0;
}

int check_win(Match * match, int last_move_colum){
    int last_row = 0;
    for (; last_row < rows; last_row++)
        if (match->grid[last_row][last_move_colum] != 0)
            break; 
        
    if (last_row == rows) return 0;

    int disc_player = match->grid[last_row][last_move_colum];

    if(check_win_colum(match, last_move_colum, last_row, disc_player)) return 1;
    if(check_win_row(match, last_move_colum, last_row, disc_player)) return 1;
    if(check_win_main_diagonal(match, last_move_colum, last_row, disc_player)) return 1;
    if(check_win_sec_diagonal(match, last_move_colum, last_row, disc_player)) return 1;
    
    return 0; 
}

int check_win_colum(Match * match, int last_move_colum, int last_row, int disc_player){
    int count = 0;
    for (int i = 0; i < 4; i++) {
        int row = last_row + i; 
        if (row < rows)
            if (match->grid[row][last_move_colum] == disc_player)
                count++;
        
    }
    return count == 4;
}

int check_win_row(Match * match, int last_move_colum, int last_row, int disc_player){
    int count, cases = 0;

    while (cases < 4) {
        count = 0;
        int start_colum = last_move_colum - cases;
        
        for (int i = 0; i < 4; i++) {
            int col = start_colum + i;
            
            if (col >= 0 && col < colums)
                if (match->grid[last_row][col] == disc_player) 
                    count++;   
        }
        
        if (count == 4) return 1;
        cases++;
    }
    return 0;
}

int check_win_main_diagonal(Match * match, int last_move_colum, int last_row, int disc_player){
    int count, cases = 0;
    int start_colum, start_row, row, col;
    while (cases < 4){
        count = 0;
        start_colum = last_move_colum - cases;
        start_row = last_row - cases;
        for (int i = 0; i < 4; i++) {
            row = start_row + i;
            col = start_colum + i;

            if ((row >= 0) && (row < rows) && (col >= 0) && (col < colums)) 
                if (match->grid[row][col] == disc_player) count++;
        
        }
    
        if (count == 4) return 1;
    
        cases++;
    }
    return 0;
}

int check_win_sec_diagonal(Match * match, int last_move_colum, int last_row, int disc_player){

        int count, start_colum, start_row, row, col, cases = 0;
        while (cases < 4){
            count = 0;
            start_colum = last_move_colum - cases;
            start_row = last_row + cases;
            for (int i = 0; i < 4; i++) {
                row = start_row - i;
                col = start_colum + i;

                if ((row >= 0) && (row < rows) && (col >= 0) && (col < colums)) 
                    if (match->grid[row][col] == disc_player) count++;
            
            }
        
            if (count == 4) return 1;
            cases++;
        }
    return 0;
}