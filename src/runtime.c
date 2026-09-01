#include <stdio.h>

/**
 * A runtime library for the Darpy Compiler
 */
#define TELETYPE_ZONE_SIZE  15
#define NUM_TELETYPE_ZONES  5
#define TELETYPE_MAX_COLUMN   TELETYPE_ZONE_SIZE * NUM_TELETYPE_ZONES


long long int current_output_column = 0;
int printed_chars = 0;
int last_printed_was_string = 0;

double dabs(double v) {
    return (v < 0) ? v * -1 : v;
}

double dfloor(double v) {
    // cast to a int to strip the decimals
    double int_part = (double)((long long)v);

    // if the number is negative and had a decimal portion, 
    // it needs to be push down by 1
    if (v < 0.0 && v != int_part) {
        int_part -= 1;
    }
    return int_part;
}


void print_basic_number(long long int int_value) {
    double value = (double)int_value;
    last_printed_was_string = 0;
    double abs_value = dabs(value);

    // is it an integer
    if (dfloor(value) == value) {
        if (abs_value <  100000000.0) {
            // Integer <= 8 digits: Print with 0 decimal places
            printed_chars = printf("%.0f", value);
        } else {
            // Integer > 8 digits: Scientific notation, 5 decimals
            printed_chars = printf("%.5E", value);
        }
    } else {
        // it is a decimal number
        printed_chars = printf("%.6g", value);
    }

    current_output_column += printed_chars;
}

void print_basic_string(const char *str) {
    last_printed_was_string = 1;
    printed_chars = printf("%s", str);
    current_output_column += printed_chars;
}

void print_newline() {
    printf("\n");
    current_output_column = 0;
}

void print_basic_comma() {
    int next_zone_col = current_output_column + (TELETYPE_ZONE_SIZE - (current_output_column % TELETYPE_ZONE_SIZE));

    if (next_zone_col >= TELETYPE_MAX_COLUMN) {
        print_newline();
    } else {
        while (current_output_column < next_zone_col) {
            printf(" ");
            current_output_column++;
        }
    }
}

void print_basic_semicolon() {
    // If the last thing printed was a number, print a space.
    // Otherwise (if it was a string), do absolutely nothing.
    if (last_printed_was_string == 0) {
        printf(" ");
        current_output_column++;
    }
}


void print_basic_tab(long long int x) {
    int target_column = x % TELETYPE_MAX_COLUMN;
    // only advances if the column hasn't already been passed
    if (target_column > current_output_column) {
        while (current_output_column < target_column) {
            printf(" ");
            current_output_column++;
        }
    }
}

void basic_sin(long long int x);
void basic_cos(long long int x);
void basic_tan(long long int x);


/**
 * Thsi is everything that I gathered for print statements

- a teletype line is 5 zones of 15 characters (aka 75 characters total)
- a comma moves to the next print zone, unless there are not more, in which chaes it moves to the first zone of the new line
- if an expression in quotes is followed by a semicolon, there is not space after it. otherwise, the object/variable is printed with a following space.
- the end of a print statement signals a newline unless followed by a semicolon or comma
- the typing format is continuous as seen on page 44 of the pdf. wherever a previous print statement left off is where the current statement will continue.

the tab function TAB(X) 
- allows for further control of spacing by jumping to the requested column, 0 tthrough 74, unless this column has been passed in output
- internally computes X modulo 75 for the column
- X can be anything but only the integer part will be taken

printing results
- if a number is an integer (regardless of type; just the decimal portion is 0), no decimal point is printed
- if an integer contains more than 8 digits, it is converted into scientfic notation with 5 decimals
- no more than 6 sigfigs are printed for decimals
- for decimals less than 0.1 and cannot fit within 6 digits, will be convert into E scientific notation
- trailling zeros are not printed

*/
