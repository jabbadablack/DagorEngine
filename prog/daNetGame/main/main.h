// Copyright (C) Gaijin Games KFT.  All rights reserved.
#pragma once

// pointer should be statically allocated string (not null); exit_code becomes the process exit code
void exit_game(const char *reason_static_str, int exit_code = 0);
void run_main_loop_frame(); //< one iteration of the main loop: game act, render (on client) and frame end
bool dng_is_app_terminating();                 //< returns true after entering post-shutdown handler

void set_window_title(const char *net_role);
const char *get_dir(const char *location);
extern bool has_in_game_editor();
bool is_initial_loading_complete();

void set_fps_limit(int max_fps);
int get_fps_limit();
void set_corrected_fps_limit(int fps_limit = -1);
