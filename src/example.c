#include <stdio.h>
#include <math.h>
#include <string.h>
#include <stdbool.h>

static bool is_integer(double x) {
    return fabs(x - floor(x)) < 1e-12;
}

static int num_digits(long long n) {
    if (n == 0) return 1;
    int d = 0;
    while (n != 0) {
        n /= 10;
        d++;
    }
    return d;
}

static void trim_trailing_zeros(char *s) {
    char *dot = strchr(s, '.');
    if (!dot) return;

    int end = strlen(s) - 1;
    while (end > (dot - s) && s[end] == '0') {
        s[end--] = '\0';
    }

    if (end == (dot - s)) {
        s[end] = '\0';   // remove decimal point
    }
}

static double round_sigfigs(double x, int sig) {
    if (x == 0.0) return 0.0;
    double exp = floor(log10(fabs(x)));
    double scale = pow(10.0, exp - sig + 1);
    return round(x / scale) * scale;
}

static bool fits_six_digits(const char *s) {
    int count = 0;
    bool started = false;

    for (int i = 0; s[i]; i++) {
        if (s[i] == '.' || s[i] == '-') continue;
        if (!started && s[i] == '0') continue;

        if (s[i] >= '0' && s[i] <= '9') {
            started = true;
            count++;
        }
    }
    return count <= 6;
}

static void normalize_leading_zero(char *s) {
    if (s[0] == '0' && s[1] == '.') {
        memmove(s, s + 1, strlen(s));
    }
    if (s[0] == '-' && s[1] == '0' && s[2] == '.') {
        s[1] = '-';
        memmove(s + 1, s + 2, strlen(s) - 1);
    }
}

static void format_scientific(double x, int decimals, char *out) {
    int exp = (int)floor(log10(fabs(x)));
    double mantissa = fabs(x) / pow(10.0, exp);

    char m[64];
    sprintf(m, "%.*f", decimals, mantissa);
    trim_trailing_zeros(m);

    sprintf(out, "%sE%+d", m, exp);
}

void basic_format(double x, char *out) {
    bool neg = x < 0;
    double v = fabs(x);

    if (v == 0.0) {
        strcpy(out, "0");
        return;
    }

    // INTEGER CASE
    if (is_integer(v)) {
        long long n = (long long)v;
        int digits = num_digits(n);

        if (digits <= 8) {
            sprintf(out, "%s%lld", neg ? "-" : "", n);
            return;
        }

        char sci[64];
        format_scientific(v, 5, sci);
        sprintf(out, "%s%s", neg ? "-" : "", sci);
        return;
    }

    // DECIMAL CASE
    double rounded = round_sigfigs(v, 6);

    if (rounded < 0.1) {
        char tmp[64];
        sprintf(tmp, "%.17g", rounded);
        trim_trailing_zeros(tmp);

        if (!fits_six_digits(tmp)) {
            char sci[64];
            format_scientific(rounded, 6, sci);
            sprintf(out, "%s%s", neg ? "-" : "", sci);
            return;
        }

        normalize_leading_zero(tmp);
        sprintf(out, "%s%s", neg ? "-" : "", tmp);
        return;
    }

    char tmp[64];
    sprintf(tmp, "%.17g", rounded);
    trim_trailing_zeros(tmp);
    normalize_leading_zero(tmp);

    sprintf(out, "%s%s", neg ? "-" : "", tmp);
}

int main() {
    char buf[128];

    basic_format(0.0000001234567, buf);
    printf("%s\n", buf);   // prints: 1.23457E-7

    basic_format(123456789, buf);
    printf("%s\n", buf);   // prints: 1.23457E+8

    basic_format(0.1234567, buf);
    printf("%s\n", buf);   // prints: .123457

    basic_format(12.34000, buf);
    printf("%s\n", buf);   // prints: 12.34
    basic_format(-0.9876543, buf);
    printf("%s\n", buf);   // prints: 12.34
    printf("%.6g\n", -0.98765437);
    printf("%.6g\n", 0.0000123456);
    return 0;
}
