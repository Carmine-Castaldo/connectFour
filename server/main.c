#include "controller/header/connectionController.h"
#include "controller/header/matchController.h"
#include "game/connectFour.h"

#define PORT 8080

int main(){
    init_matchController();
    int fd_server = init_server(PORT);
    return 0;
}

