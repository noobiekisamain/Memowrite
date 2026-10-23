# Memowrite — Everything You Can Do

Memowrite is a programming language written in plain English words. Every line starts with a
command word like `say`, `set`, `if`, `repeat`, `draw` or `add`, and blocks finish with `end`.

* Files end in **.mw**. Run one by double-clicking it, pressing **F5** in Memowrite Studio,
  pressing **Ctrl+F5** in Visual Studio Code, or typing `memowrite myprogram.mw` in a terminal.
* Capital letters don't matter for commands or names (`Say`, `SAY` and `say` are the same).
* Comments start with `#`, `//` or the word `note`.
* A very long line can carry on to the next line if it ends with `...`
* Lists count from **1** (the first item is item 1, the last item is item -1).
* There are 25 ready-made programs in the **examples** folder — open them from Studio's **Examples** menu.

---

## 1. Showing and asking

- Show text: `say "Hello!"`
- Show several things: `say "Score:", score, "Lives:", lives`
- Put values inside text with curly brackets: `say "Hi {name}, you are {age + 1} next year"`
- Stay on the same line: `say "Loading" without newline`
- Ask a question and keep the answer: `ask "What is your name?" into name`
  (answers that look like numbers become numbers automatically)
- Force the kind of answer: `ask "Your PIN?" into pin as text` or `ask "Age?" into age as number`
- Ask in a popup box: `ask "Your name?" in a popup into name`
- Debug output (shows the line number): `whisper score`
- Clear the screen: `clear screen`
- Colored text: `color text "green"` … `color text "normal"`
- Show a popup: `show message "Saved!"`, `show warning "Careful"`, `show error "Oh no"`, `show message "Hi" titled "Hello"`
- Ask yes or no in a popup: `if confirm("Delete everything?") then ...`

## 2. Values and names (variables)

- Give a name a value: `set score to 0` / `let score be 0` / `score = 0`
- Kinds of values: numbers `42`, `3.5`; text `"hello"` or `'hello'`; yes/no `yes`, `no`, `true`, `false`;
  `nothing`; lists `[1, 2, 3]`; books `{"name": "Rex", "age": 3}`
- Change a number: `change score by 5`, `add 5 to score`, `take 2 from score`, `subtract 2 from score`,
  `multiply score by 2`, `divide score by 4`, `increase lives`, `decrease lives by 2`
- Join text onto text: `add "!" to message`
- Swap two values: `swap a and b`
- Escape characters in text: `\n` new line, `\t` tab, `\"` quote, `\{` a real curly bracket
- `pi` is 3.14159…, `percent`: `50 percent` is 0.5

## 3. Maths

- Symbols: `+ - * / % ^` and words: `plus`, `minus`, `times`, `multiplied by`, `divided by`, `mod`,
  `remainder of`, `to the power of`, `squared`, `cubed`
- `the square root of 81`, `sqrt(81)`, `round(3.14159, 2)`, `floor`, `ceiling`, `abs`, `whole(7.9)`
- `max(…)`, `min(…)`, `sum(list)`, `average(list)`, `median(list)`, `clamp(x, 0, 10)`, `lerp(a, b, 0.5)`
- `sin`, `cos`, `tan` (in degrees), `atan(y, x)`, `log`, `ln`, `exp`, `power(2, 10)`
- `is_prime(7)`, `factorial(5)`, `gcd(12, 18)`, `lcm(4, 6)`, `fibonacci(10)`
- `distance(x1, y1, x2, y2)`, `angle_between(x1, y1, x2, y2)`
- `binary(10)`, `hex(255)`, `from_binary("1010")`, `from_hex("ff")`
- `commas(1234567)` → `1,234,567`, `money(5)` → `5.00`, `spell_number(42)` → `forty-two`, `ordinal(3)` → `3rd`

## 4. Random things

- `random number from 1 to 6`, `random(1, 100)`, `random()` (between 0 and 1)
- `a random item from fruits`, `pick(fruits)`, `pick("rock", "paper", "scissors")`
- `dice()`, `dice(20)`, `chance(30)` (yes 30% of the time), `coin_flip()`
- `random_color()`, `random_name()`, `random_word()`, `password(12)`, `uuid()`
- `shuffle cards`, `shuffled(cards)`, `seed(42)` makes randomness repeatable

## 5. Comparing and deciding

- `if score is 10 then … end` (one line: `if score is 10 then say "ten!"`)
- `otherwise if …`, `otherwise` (or `else if`, `else`)
- `unless lives is 0 … end`
- Comparisons: `is`, `is not`, `is more than`, `is greater than`, `is bigger than`, `is above`,
  `is less than`, `is smaller than`, `is below`, `is at least`, `is at most`, `is equal to`,
  `is between 1 and 10`, `is divisible by 3`, `is even`, `is odd`, `is empty`, `is not empty`,
  `is nothing`, `is in list`, `is a number`, `is a text`, `is a list`, `is a book`,
  `contains`, `does not contain`, `starts with`, `ends with`, `touches` (shapes) — and `== != > < >= <=`
- Text comparisons ignore capital letters: `"YES" is "yes"` is yes
- Combine with `and`, `or`, `not`
- Pick between many choices:

  ```
  check answer
      is "red", "orange"
          say "warm"
      is "blue"
          say "cool"
      otherwise
          say "hmm"
  end
  ```

## 6. Loops (doing things again)

- `repeat 5 times … end`
- `repeat while lives is more than 0 … end` / `while … end`
- `repeat until done … end` / `until … end`
- `repeat forever … end` / `forever … end`
- `count i from 1 to 10 … end`, `count i from 10 down to 0 by 2 … end`
- `for each fruit in fruits … end` (also works on text letters, book keys and numbers)
- `for each position, fruit in fruits … end` (gives the position too)
- Leave a loop: `stop` — skip to the next turn: `skip` — end the whole program: `stop program`
- `do greet 3 times`

## 7. Tasks (your own commands)

- Make one: `make task greet with who … end` (also `to greet with who`, `make task greet(who)`)
- Run it: `do greet with "Sam"`, `greet("Sam")`, `call greet with "Sam"`, or just `greet` when it needs nothing
- Give a value back: `give back x * 2` (or `return x * 2`)
- Tasks can call themselves (recursion) and be used before the line that makes them
- Tasks are values: `map(numbers, double)`, `filter(numbers, is_even)`, `sort_by(people, age_of)`
- Run a task at the same time as the rest of the program: `do download_all in the background`
- Use code from another file: `use "my_tasks.mw"`
- Built-in libraries: `use "helpers"` (ask_number, ask_yes_no, choose_from, press_enter, type_slowly) and
  `use "shapes"` (ready-made models: house, tree, flower, cloud, rocket)

## 8. Lists

- `make list fruits with "apple", "pear"`, `set empty to []`, `an empty list`
- Add: `put "kiwi" into fruits`, `add "kiwi" to fruits`, `put "fig" into fruits at position 1`
- Read: `item 2 of fruits`, `fruits[2]`, `first item of fruits`, `last of fruits`, `fruits[-1]`, `fruits[2:4]`
- Change: `set fruits[1] to "plum"`
- Remove: `remove "kiwi" from fruits`, `remove item 2 from fruits`, `remove last item from fruits`, `empty fruits`
- Sort: `sort fruits`, `sort fruits backwards`, `sort people by "age"`, `reverse fruits`, `shuffle fruits`
- Ask: `length of fruits`, `fruits contains "fig"`, `find(fruits, "fig")`, `count(list, item)`
- Make new lists: `range(1, 10)`, `sorted`, `reversed`, `unique`, `flatten`, `take`, `drop`, `zip`, `chunk`,
  `fill_list(3, 0)`, `grid_of(rows, columns, value)`, `map`, `filter`, `reduce`, `tally`, `most_common`, `group_by`
- `join(fruits, ", ")` turns a list into text; `split("a,b", ",")` turns text into a list

## 9. Books (named values, like a dictionary)

- `make book pet with name as "Rex", age as 3` or `set pet to {"name": "Rex", "age": 3}`
- Read: `name of pet`, `pet.name`, `pet["name"]`
- Change or add: `set pet["age"] to 4`, `set colour of pet to "brown"`, `pet.age = 5`
- `keys of pet`, `values of pet`, `has_key(pet, "age")`, `remove "age" from pet`, `merge(a, b)`
- `for each key in pet … end`

## 10. Kinds (blueprints for things)

```
make kind pet with name, sound
    make task speak
        say my name + " says " + my sound
    end
end
set rex to pet("Rex", "woof")
rex.speak()
set rex.sound to "WOOF"
```

- Inside a kind's tasks, `my name` / `me` mean "this thing"
- A task called `setup` runs automatically when a new thing is made

## 11. Text

- `length of`, `uppercase of`, `lowercase of`, `titlecase`, `capitalize`, `trim`, `reversed`
- `replace(text, "old", "new")`, `split`, `join`, `part(text, 2, 5)`, `left(text, 3)`, `right(text, 3)`
- `letter 1 of name`, `word 2 of sentence`, `line 3 of story`, `first word of`, `last word of`
- `words in`, `letters in`, `lines in`, `count_words`, `count_vowels`, `find(text, "x")`
- `text contains "x"`, `starts with`, `ends with`, `is_palindrome`, `is_email`, `is_number`
- `pad_left("7", 3, "0")` → `007`, `center`, `repeat_text("ha", 3)`, `slug`, `format("{} and {}", a, b)`
- Patterns: `matches(text, "[0-9]+")`, `find_all(text, "[a-z]+")`
- Fun: `caesar`, `decode_caesar`, `morse`, `banner("HI")`, `box("text")`, `table(rows)`, `progress_bar(3, 10)`, `wrap`, `underline`
- `code_of("A")`, `letter_of_code(65)`, `base64`, `hash`, `plural(3, "cat")`
- Convert: `x as number`, `x as text`, `number("12")`, `text(12)`, `bool(x)`, `typeof(x)`

## 12. File.Memory (remember things forever)

Every program has a **File.Memory** file next to it. Things you `remember` are still there
the next time the program runs — even after restarting the computer.

- `remember "high score" as 120`
- `remember score` (saves the variable under its own name)
- `recall "high score" into best` / `recall "high score" into best or 0` (0 if nothing was saved)
- `recall score` (loads it back into the same name)
- `forget "high score"`, `forget everything`
- `memory("high score")`, `memory_keys()`, `remembers("high score")`
- File.Memory is plain, readable JSON — you can open it in any editor

## 13. Files and folders

- `write "Hello" to file "notes.txt"` (replaces the file)
- `add "another line" to file "notes.txt"` / `append "…" to file "notes.txt"`
- `read file "notes.txt" into notes`, `read lines of file "notes.txt" into lines`, `read_file("x.txt")`
- `save scores to "scores.json"` and `load "scores.json" into scores` (lists and books keep their shape)
- `save rows to "people.csv"` / `load "people.csv" into rows` (spreadsheets)
- `delete file "old.txt"`, `delete folder "temp"`, `make folder "saves"`
- `copy file "a.txt" to "b.txt"`, `rename file "a.txt" to "c.txt"`
- `file_exists("x.txt")`, `folder_exists`, `files_in("folder")`, `folders_in`, `search_files("*.mw")`,
  `file_size`, `file_modified`, `count_lines`, `file_name`, `file_extension`, `full_path`
- Special folders: `home_folder()`, `desktop_folder()`, `documents_folder()`, `downloads_folder()`, `program_folder()`
- Let the user choose: `pick_file()`, `pick_save_file()`, `pick_folder()`
- Open a file, folder or website: `open "picture.png"`, `open "https://example.com"`
- Internet: `fetch page "https://example.com" into html`, `fetch_json(url)`,
  `download "https://…/cat.png" into file "cat.png"`
- Clipboard: `copy "hello" to clipboard`, `clipboard()`

## 14. Time and waiting

- `wait 2 seconds`, `wait 500 milliseconds`, `wait a second`, `pause 1 minute`
- `now()`, `today()`, `time()`, `year()`, `month()`, `month_name()`, `day()`, `weekday()`, `hour()`, `minute()`, `second()`
- `timer()` seconds since the program started, `milliseconds()`, `timestamp()`
- `days_between("2026-01-01", "2026-12-25")`, `days_until("2026-12-24")`, `add_days(today(), 7)`,
  `format_date(today())`, `age_from("1990-05-01")`, `is_leap_year(2028)`, `duration(125)` → `2:05`
- Repeat on a timer: `every 1 second do tick` or

  ```
  every 500 milliseconds
      say "tick"
  end
  ```
- Run once later: `after 3 seconds do surprise`
- `stop all timers`

## 15. Errors (when things go wrong)

```
try
    read file "missing.txt" into text
if it fails as problem
    say "Could not read it: " + problem
end
```

- Make your own error: `complain "That is not allowed!"`
- Check something must be true: `ensure age is a number or complain "Age must be a number"`
- Mistakes show a friendly message with the line number, and often a tip like *Did you mean 'score'?*
- Check a program without running it: **F7** in Studio, or `memowrite check game.mw`

## 16. Sound and speech

- `beep`, `beep 3 times`
- `play note "c" for 300 milliseconds`, `play note "a5" for 1 second`, `play note 440 for 200 milliseconds`
- `play sound "win.wav"`, `play music "theme.wav" forever`, `stop music`
- `speak "Hello, I am your computer"` (talks out loud on Windows)

## 17. Window apps

```
make window app titled "My App" sized 420 by 320
add heading title to app saying "Hello!"
add input box nameBox to app placeholder "Your name"
add button go to app saying "Greet me" doing greet
add label answer to app saying ""

make task greet
    set text of answer to "Hi " + text of nameBox
end
```

- Windows: `make window app titled "…" sized 400 by 300`, options `color "navy"`, `dark`, `fixed`, `fullscreen`,
  `icon "my.ico"`, `at 100, 100`. More windows can be made at any time. `show app`, `hide app`, `close app`
- Window settings: `set title of app to "…"`, `set background of app to "…"`, `set opacity of app to 90`,
  `set on_top of app to yes`, `width of app`, `height of app`
- Parts you can add (all with `add KIND NAME to WINDOW …`):
  - `label`, `heading`, `button`, `input box`, `password`, `text box` (many lines), `checkbox`,
    `slider` (`from 0 to 100`, `step 5`), `dropdown` (`with ["a", "b"]`), `list box`, `radio` (`with […]`),
    `number box`/`spinner`, `progress` bar, `table` (`columns "Name", "Age"`), `image` (`with "cat.png"`),
    `canvas` (for drawing), `link` (`with "https://…"`), `color picker`, `separator`, `space`
  - Layout: `panel` (a box of parts, `saying "Title"` gives it a heading), `row` (puts parts side by side),
    `tabs` + `tab` (pages)
- Options for parts: `saying "text"`, `doing taskname`, `at x, y`, `sized w by h`, `color "…"`, `background "…"`,
  `font "…"`, `bold`, `big`, `small`, `tip "hover help"`, `placeholder "…"`, `value …`, `rows 10`, `wrap`, `readonly`, `centered`
- Read and change parts: `text of nameBox`, `value of slider`, `checked of box`, `items of list`, `selected of list`,
  `number of input`, `set text of label to "…"`, `set color of label to "red"`, `set background of button to "green"`,
  `set size of label to 20`, `set items of dropdown to […]`, `add "x" to listbox`, `remove "x" from listbox`, `clear listbox`
- `hide button`, `show button`, `disable button`, `enable button`, `focus on nameBox`, `delete button`
- Events: `when go is clicked do play`, `when slider is changed do update`, `when box is submitted do send`,
  `when list is double clicked do open_it`, `when app is closed do save_all`, `when app is resized do relayout`,
  `when key "space" is pressed do jump`, `when key "left" is released in app do stop_moving`, `when any key is pressed do typed`,
  `when mouse is clicked on board do click`, `when mouse moves on board do follow`, `when mouse is dragged on board do paint`,
  `when mouse is released on board do lift`, `when mouse is right clicked on board do menu`, `when ball is clicked do pop`
  — tasks for mouse events get `x, y`; key events get the key name; changes get the new value
- Event blocks without a separate task:

  ```
  when go is clicked
      say "clicked!"
  end
  ```
- Buttons that share a task get their own text: `make task pressed with key` (see the calculator example)
- Menus: `menu "File" in app with "Open" doing open_it, "Quit" doing quit_it`
- Keys and mouse at any time: `key_down("left")`, `keys_pressed()`, `mouse_x()`, `mouse_y()`
- `screen_width()`, `screen_height()`

## 18. 2D drawing

- Make a canvas in a window: `add canvas board to app sized 600 by 400 background "sky"`
- Or a picture without a window: `make picture art sized 800 by 600 background "white"`
- If you draw before making a canvas, a drawing window opens by itself
- Shapes: `circle`, `ellipse`/`oval`, `rectangle`/`box`, `square`, `roundbox`, `triangle`, `polygon`, `star`,
  `heart`, `hexagon`, `pentagon`, `diamond`, `ring`, `arc`, `dot`, `line`, `arrow`, `path`, `grid`, `text`, `image`

  ```
  draw circle at 100, 100 size 40 color "red" called ball
  draw rectangle on board at 10, 300 size 600 by 40 color "grass"
  draw line from 0, 0 to 200, 150 color "black" width 3 dashed
  draw text at 300, 40 saying "Hello" size 24 bold color "navy"
  draw star at 200, 80 size 30 color "gold" angle 15
  draw polygon points [[0, 0], [60, 0], [30, 50]] at 100, 100 color "purple"
  draw image "cat.png" at 200, 200
  ```
- Positions: circles, stars, text and most shapes use their **centre**; rectangles, squares and roundboxes use their **top-left corner**
- Sizes: circle `size` = radius; ellipse/rectangle `size W by H`; square, star, hexagon `size` = one number; text `size` = font size
- Shape options: `color`, `outline`, `width`, `angle`, `called`, `dashed`, `smooth`, `corner` (roundbox), `start` and `extent` (arc),
  `spacing` (grid), `points` (polygon, path, or number of star tips), `font`, `bold`, `hidden`
- Colors: all web color names (`"tomato"`, `"sky blue"`), friendly ones (`"grass"`, `"sun"`, `"night"`, `"wood"`, `"leaf"`),
  `"light red"`, `"dark blue"`, codes like `"#ff8800"`, `rgb(255, 128, 0)`, `hsl(200, 80, 50)`, `lighter(c)`, `darker(c)`,
  `mix_colors(a, b)`, `random_color()`, and `nothing` for no fill
- `fill board with "black"`, `clear board`, `shape_count()`, `canvas_width()`, `canvas_height()`
- Save pictures: `export board to "picture.png"` (also `.svg`, `.ppm`, `.mwpic`, `.ps`)

## 19. 2D models (shapes that belong together)

```
make model car
    roundbox at -45, -18 size 90 by 26 color "crimson"
    circle at -25, 10 size 11 color "black"
    circle at 25, 10 size 11 color "black"
end
place model car on board at 200, 300 called myCar
place model car at 400, 300 size 1.5 color "royalblue" angle 10 called bigCar
```

- Model parts use positions around the model's centre (0, 0)
- `save model car to "car.mwmodel"` and `load model car from "car.mwmodel"` — share models between programs
- `model_from(shape1, shape2)` turns shapes you already drew into a model
- `width of car`, `height of car`, `parts of car`

## 20. Moving and changing shapes (animation)

- `move ball by 5, 0`, `move ball to 300, 200`, `move ball left 10` (also right, up, down)
- `move ship forward 5` (in the direction it is facing), `move enemy towards x of player, y of player by 3`
- `rotate car by 45`, `rotate car to 90`, `turn robot left 15`, `turn robot right 15`
- `scale tree by 1.5`, `grow tree by 2`, `resize box to 100 by 50`, `flip car horizontally`, `flip car vertically`
- `recolor ball to "blue"`, `set color of ball to "blue"`, `set outline of ball to "white"`, `set text of label to "…"`
- `hide ball`, `show ball`, `delete ball`, `bring ball to front`, `send ball to back`, `clone(ball)`
- `animate ball to 400, 300 over 2 seconds`
- `bounce ball inside board using dx, dy` (flips your speed numbers when the ball hits an edge)
- Read where a shape is: `x of ball`, `y of ball`, `left of`, `right of`, `top of`, `bottom of`, `width of`, `height of`, `angle of`
- Store your own facts on a shape: `set ball.speed to 4`, `say ball.speed`
- Collisions: `if ball touches paddle then …`, `ball touches "edge"`, `touching_edge(ball)`, `point_inside(ball, x, y)`
- Game loop: `every 16 milliseconds do update` (about 60 frames a second), or `repeat forever … wait 16 milliseconds … end`

## 21. Your computer

- `username()`, `computer_name()`, `operating_system()`, `language()`, `cpu_count()`, `environment("PATH")`
- `arguments` — words typed after the program name: `memowrite greet.mw Bob`
- `version()` — the Memowrite version
- `quit` / `exit` / `stop program`

## 22. Tools that come with Memowrite

- **Memowrite Studio** — the editor: syntax colors, line numbers, Run (F5), Stop (Shift+F5), Check (F7), Find (Ctrl+F),
  comment lines (Ctrl+/), zoom (Ctrl+ / Ctrl−), Examples and Insert menus, an answer box for `ask`, click a red error to jump to it
- **memowrite** command (added to PATH by the installer):
  `memowrite game.mw`, `memowrite run game.mw`, `memowrite check game.mw`, `memowrite new MyGame`,
  `memowrite words` (every built-in word), `memowrite studio`, `memowrite` (the interactive shell), `memowrite version`
- **Visual Studio Code extension** — colors, snippets (type `window`, `model`, `game`… then Tab), Run button, Ctrl+F5, F7 check on save, `.mw` file icon
- **Visual Studio 2019/2022** — Memowrite syntax colors for `.mw` files
- Double-click any `.mw` file to run it; right-click → *Edit with Memowrite Studio*

## 23. The example programs

| File | What it shows |
|---|---|
| 01_hello.mw | say, ask, text with {names} |
| 02_numbers_and_maths.mw | maths in words and symbols |
| 03_decisions.mw | if / otherwise / check |
| 04_loops.mw | repeat, count, for each, stop, skip |
| 05_lists_and_books.mw | lists and books |
| 06_tasks.mw | your own commands, recursion |
| 07_guessing_game.mw | a game with a record in File.Memory |
| 08_file_memory.mw | remembering things forever |
| 09_files.mw | text, JSON and CSV files |
| 10_text_tricks.mw | banners, boxes, codes, colors |
| 11_calculator_app.mw | a calculator window app |
| 12_todo_app.mw | a to-do app that saves itself |
| 13_drawing.mw | drawing a picture and exporting PNG/SVG |
| 14_2d_models.mw | 2D models: trees, cars, a robot |
| 15_bouncing_ball.mw | animation and mouse clicks |
| 16_catch_game.mw | a keyboard game with a high score |
| 17_paint_app.mw | a paint program |
| 18_kinds.mw | kinds (blueprints) |
| 19_errors.mw | try / if it fails / complain / ensure |
| 20_clock_app.mw | a clock and stopwatch with timers |
| 21_quiz.mw | a quiz from a list of books |
| 22_notes_app.mw | tabs, menus, text editor, files |
| 23_art_generator.mw | generative art saved as PNG |
| 24_contact_book.mw | tables and saved contacts |
| 25_solar_system.mw | orbiting planets with sin and cos |

---

## 24. Every built-in word

Use any of these like `length of "hello"` or `length("hello")`. Words in brackets are other names for the same thing.

