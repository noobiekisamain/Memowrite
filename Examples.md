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

- **abs** — Makes a number positive *(also: absolute, positive)*
- **acos** — Angle (degrees) whose cosine is x *(also: arccos)*
- **add_days** — add_days("2026-01-01", 10)
- **age_from** — Age in years from a birth date *(also: age)*
- **all** — Are all items true (or true for the task)? *(also: all_true, every_one)*
- **angle_between** — Angle in degrees from point 1 to point 2 *(also: direction)*
- **any** — Is any item true (or true for the task)? *(also: any_true)*
- **asin** — Angle (degrees) whose sine is x *(also: arcsin)*
- **atan** — Angle (degrees) of a slope, atan(y, x) also works *(also: arctan)*
- **average** — The average of numbers *(also: mean)*
- **banner** — Big block letters
- **base64** — Encodes text as base64 *(also: encode_base64)*
- **binary** — A number written in binary
- **book** — book("name", "Bob", "age", 3) *(also: dictionary, make_book)*
- **bool** — Turns a value into yes or no *(also: truth, yes_or_no)*
- **box** — Draws a box around text
- **caesar** — Shifts letters to make a secret code *(also: encode_caesar, secret_code)*
- **canvas_height** — Height of the canvas
- **canvas_width** — Width of the canvas
- **capitalize** — Hello world *(also: capitalise, sentence_case)*
- **ceiling** — Rounds up *(also: ceil, roundup)*
- **center** — Centers text in a width *(also: centre)*
- **chance** — chance(30) is yes 30% of the time *(also: coin_flip, flip_coin)*
- **chunk** — Splits a list into groups of n *(also: groups_of)*
- **clamp** — clamp(x, low, high) keeps x between low and high *(also: keep_between, limit)*
- **clipboard** — The text on the clipboard
- **clone** — Makes a copy of a shape on the same canvas
- **code_of** — The number code of a letter *(also: ascii, char_code)*
- **color_code** — The #rrggbb code of a color name
- **computer_name** — The name of this computer
- **confirm** — Asks a yes/no question in a popup
- **contains** — Does the text or list contain something? *(also: has_text, includes)*
- **copy** — A copy of a list or book *(also: copy_of, duplicate)*
- **cos** — Cosine of an angle in degrees *(also: cosine)*
- **count** — How many times something appears *(also: count_of_text, occurrences)*
- **count_lines** — How many lines a file has
- **count_vowels** — How many vowels
- **count_words** — How many words *(also: word_count)*
- **countdown_text** — 125 seconds -> 2:05 *(also: duration)*
- **cpu_count** — How many processor cores the computer has
- **darker** — A darker version of a color
- **day** — Day of the month
- **days_between** — Days between two dates (or until a date) *(also: days_until)*
- **decode_base64** — Decodes base64 text
- **decode_caesar** — Undoes caesar()
- **default** — default(x, 0) gives 0 if x is nothing *(also: or_else, otherwise_use)*
- **degrees** — Radians to degrees
- **desktop_folder** — Your Desktop folder
- **dice** — Roll a dice (6 sides by default) *(also: roll, roll_dice)*
- **distance** — distance(x1, y1, x2, y2)
- **documents_folder** — Your Documents folder
- **downloads_folder** — Your Downloads folder
- **drop** — drop(list, 2) - all but the first 2 items *(also: skip_n)*
- **e** — The number e
- **ends_with** — Does the text end with ...? *(also: endswith)*
- **engine_version** — The version of the engine Memowrite runs on
- **environment** — Reads an environment setting
- **exp** — e to the power of x
- **factorial** — 5 factorial is 120
- **fetch** — Gets the text of a web page
- **fetch_json** — Gets JSON data from the internet
- **fibonacci** — The n-th Fibonacci number *(also: fib)*
- **file_exists** — Is there a file with this name?
- **file_extension** — The end of a file name, like txt
- **file_modified** — When a file was last changed
- **file_name** — Just the name part of a path
- **file_size** — Size of a file in bytes
- **files_in** — List of files in a folder
- **fill_list** — fill_list(3, 0) gives [0, 0, 0] *(also: list_of)*
- **filter** — filter(list, task) keeps items where the task gives yes *(also: keep, only, select)*
- **find** — Position (from 1) of something, or 0 *(also: index_of, position, position_of, where_is)*
- **find_all** — All pieces of text matching a pattern *(also: regex_find)*
- **first** — The first item
- **first_line** — The first line
- **first_word** — The first word
- **flatten** — Turns a list of lists into one list
- **floor** — Rounds down *(also: rounddown)*
- **folder_exists** — Is there a folder with this name?
- **folders_in** — List of folders in a folder
- **format** — format("{} has {}", "Bob", 3) *(also: fill_in)*
- **format_date** — format_date("2026-10-23") -> "Friday 23 October 2026" *(also: pretty_date)*
- **format_number** — 1234567 -> 1,234,567 *(also: commas, with_commas)*
- **from_binary** — Binary text to a number
- **from_csv** — Turns CSV text into a list of lists *(also: parse_csv)*
- **from_hex** — Hexadecimal text to a number
- **from_json** — Turns JSON text into lists and books *(also: parse_json)*
- **full_path** — The full path of a file
- **gcd** — Greatest common divisor *(also: greatest_common_divisor)*
- **get_or** — get(book, key, default) *(also: get, lookup)*
- **grid_of** — grid_of(rows, columns, value) - a list of lists *(also: make_grid)*
- **group_by** — group_by(list, "type") makes a book of lists
- **has_key** — Does the book have this key? *(also: has)*
- **hash** — A short fingerprint (sha256) of some text *(also: fingerprint)*
- **hex** — A number written in hexadecimal *(also: hexadecimal)*
- **home_folder** — Your home folder
- **hour** — The hour now (0-23)
- **hsl** — hsl(200, 80, 50) makes a color from hue, saturation, lightness
- **indent** — Indents every line
- **index_list** — [a, b] -> [[1, a], [2, b]] *(also: numbered)*
- **is_book** — Is this a book?
- **is_email** — Does it look like an email address? *(also: looks_like_email)*
- **is_even** — Is the number even? *(also: even)*
- **is_leap_year** — Is it a leap year? *(also: leap_year)*
- **is_letter** — Is this text only letters? *(also: is_alpha, is_letters)*
- **is_list** — Is this a list?
- **is_lower** — Is the text in small letters?
- **is_nothing** — Is this nothing? *(also: is_none)*
- **is_number** — Is this a number (or text that is a number)? *(also: is_numeric, isnumber)*
- **is_odd** — Is the number odd? *(also: odd)*
- **is_palindrome** — Is it the same backwards? *(also: palindrome)*
- **is_prime** — Is the number prime? *(also: prime)*
- **is_text** — Is this text?
- **is_upper** — Is the text in capitals?
- **is_vowel** — Is the letter a vowel?
- **join** — join([a, b], ", ") gives "a, b" *(also: glue, joined)*
- **key_down** — Is this key held down right now?
- **keys** — The keys of a book *(also: fields, names_in)*
- **keys_pressed** — All keys held down right now
- **language** — The computer's language setting
- **last** — The last item
- **last_line** — The last line
- **last_word** — The last word
- **lcm** — Least common multiple
- **left** — left("hello", 2) gives "he" *(also: first_letters)*
- **length** — How many items or letters *(also: count_of, how_many, len, size)*
- **lerp** — lerp(a, b, 0.5) is halfway between a and b *(also: blend, mix)*
- **letter_of_code** — The letter with a number code *(also: char, from_code)*
- **letters** — The letters in a text as a list *(also: characters, chars)*
- **lighter** — A lighter version of a color
- **line_at** — line 2 of a text
- **lines** — The lines in a text as a list
- **list** — list(1, 2, 3) or list of a text *(also: make_list, tolist)*
- **ln** — Natural logarithm *(also: naturallog)*
- **log** — Logarithm (base 10 by default) *(also: logarithm)*
- **lowercase** — hello *(also: lower)*
- **map** — map(list, task) runs a task on every item *(also: each_changed, transform)*
- **matches** — Does text match a pattern (regular expression)? *(also: matches_pattern, regex_match)*
- **max** — The biggest value *(also: biggest, highest, largest)*
- **median** — The middle value of a list of numbers *(also: middle)*
- **memory** — memory("score") reads a value from File.Memory *(also: recall_value, remembered)*
- **memory_keys** — Everything saved in File.Memory *(also: remembered_names)*
- **merge** — Merges two books *(also: merged)*
- **milliseconds** — Milliseconds since the program started *(also: ms_now)*
- **min** — The smallest value *(also: least, lowest, smallest)*
- **minute** — The minute now
- **mix_colors** — Mixes two colors
- **model_from** — Turns drawn shapes into a reusable model
- **money** — money(5) -> 5.00 *(also: currency)*
- **month** — This month (1-12)
- **month_name** — The name of this month (or of month n)
- **morse** — Turns text into Morse code *(also: to_morse)*
- **most_common** — The item that appears most often *(also: mode)*
- **mouse_x** — Where the mouse is (left-right) on the canvas
- **mouse_y** — Where the mouse is (up-down) on the canvas
- **now** — The date and time now as text *(also: time_now)*
- **number** — Turns text into a number *(also: num, tonumber)*
- **only_digits** — Keeps only the digits *(also: only_numbers)*
- **only_letters** — Keeps only the letters
- **operating_system** — Windows 11, etc.
- **ordinal** — 1 -> 1st, 2 -> 2nd
- **pad_left** — pad_left("7", 3, "0") gives "007" *(also: pad)*
- **pad_right** — pad_right("hi", 5) gives "hi   "
- **part** — part("hello", 2, 4) gives "ell" *(also: middle_of, slice, substring)*
- **password** — A random strong password *(also: make_password, random_password)*
- **percent** — percent(25, 200) is 12.5 *(also: percentage)*
- **pick** — A random item from a list *(also: any_of, choose, random_item)*
- **pick_file** — Lets the user choose a file
- **pick_folder** — Lets the user choose a folder
- **pick_save_file** — Lets the user choose where to save
- **plural** — plural(3, "cat") -> "3 cats"
- **point_inside** — Is the point inside the shape?
- **power** — power(2, 3) is 8 *(also: pow)*
- **program_folder** — The folder your program is in *(also: this_folder)*
- **progress_bar** — A text progress bar like [#####-----] 50%
- **radians** — Degrees to radians
- **random** — random(1, 6) gives a whole number from 1 to 6 *(also: rand, random_number)*
- **random_color** — A random bright color *(also: random_colour)*
- **random_name** — A random friendly name
- **random_word** — A random English word
- **range** — range(1, 5) gives [1, 2, 3, 4, 5] *(also: numbers, numbers_from)*
- **read_file** — The text inside a file
- **reduce** — reduce(list, task, start) *(also: combine, fold)*
- **remembers** — Is this name saved in File.Memory? *(also: in_memory)*
- **remove_spaces** — Removes all spaces *(also: nospaces)*
- **repeat_text** — repeat_text("ha", 3) gives "hahaha" *(also: repeated)*
- **replace** — replace(text, "old", "new") *(also: replaced, swap_text)*
- **rest** — Everything except the first item *(also: all_but_first)*
- **reversed** — olleh / reversed list *(also: backwards, reverse)*
- **rgb** — rgb(255, 128, 0) makes a color
- **right** — right("hello", 2) gives "lo" *(also: last_letters)*
- **round** — round(3.7) is 4, round(3.14159, 2) is 3.14 *(also: rounded)*
- **run_task** — run_task(mytask, value1, value2 ...) *(also: call_task)*
- **screen_height** — Height of the screen in pixels
- **screen_width** — Width of the screen in pixels
- **search_files** — Finds files matching a pattern like *.txt
- **second** — The second now
- **seed** — Makes random numbers repeatable *(also: set_seed)*
- **shape_count** — How many shapes are on a canvas
- **shuffled** — A shuffled copy of a list
- **sign** — -1, 0 or 1
- **sin** — Sine of an angle in degrees *(also: sine)*
- **slug** — "Hello World!" -> "hello-world" *(also: url_name)*
- **sort_by** — sort_by(list, "age") sorts books by a field
- **sorted** — A sorted copy of a list *(also: sort_list)*
- **spell_number** — 42 -> forty-two *(also: in_words, number_to_words)*
- **split** — split("a,b", ",") gives [a, b] *(also: split_text)*
- **sqrt** — Square root of a number *(also: root, squareroot)*
- **stars** — A row of stars
- **starts_with** — Does the text start with ...? *(also: begins_with, startswith)*
- **sum** — Adds up all the numbers *(also: add_up, total)*
- **table** — Makes a text table from a list of lists
- **take** — take(list, 3) - the first 3 items *(also: first_n)*
- **tally** — A book of how many times each item appears *(also: counts)*
- **tan** — Tangent of an angle in degrees *(also: tangent)*
- **text** — Turns anything into text *(also: str, string, totext)*
- **time** — The time now, like 14:05 *(also: clock)*
- **timer** — Seconds since the program started *(also: elapsed, running_time, seconds_running)*
- **timestamp** — Seconds since 1970 *(also: seconds_since_1970)*
- **titlecase** — Hello World *(also: capitalize_words, title_case)*
- **to_csv** — Turns a list of lists into CSV text
- **to_json** — Turns a value into JSON text *(also: json)*
- **today** — Today's date, like 2026-10-23 *(also: date)*
- **touching** — Do two shapes touch?
- **touching_edge** — Is the shape at the edge of its canvas?
- **trim** — Removes spaces at the start and end *(also: strip, tidy, trimmed)*
- **typeof** — What kind of value this is *(also: kind_of, type, what_is)*
- **underline** — Text with a line under it
- **unique** — The list without repeated items *(also: distinct, no_duplicates)*
- **uppercase** — HELLO *(also: capitals, shout_text, upper)*
- **username** — Your user name on this computer
- **uuid** — A unique id text *(also: unique_id)*
- **values** — The values of a book
- **version** — The Memowrite version *(also: memowrite_version)*
- **weekday** — Monday, Tuesday ... (today or a date) *(also: day_name, day_of_week)*
- **whole** — Drops the decimals *(also: int, integer, wholenumber)*
- **window_is_open** — Is any window still open?
- **word_at** — word 2 of a sentence
- **words** — The words in a text as a list
- **wrap** — Wraps long text into lines
- **year** — This year
- **zip** — Pairs two lists together *(also: pair_up)*

*241 built-in words, 443 names in total.*
