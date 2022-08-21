class TimeForm:
    def __init__(self, stamp):
        self.stamp = stamp
        self.stamp_copy = self.stamp
        self.year = 0
        self.month = 0
        self.day = 0
        self.hour = 0
        self.minute = 0
        self.second = 0
        self.sub_second = 0
        self.clock = 'AM'
        self.months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                       'November', 'December']
        self.days = ['Thursday', 'Friday', 'Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday']
        self.month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    def reset(self):
        self.stamp_copy = self.stamp
        self.year = 0
        self.month = 0
        self.day = 0
        self.hour = 0
        self.minute = 0
        self.second = 0
        self.sub_second = 0
        self.clock = 'AM'

    def leap_year(self):
        if self.year % 400 == 0:
            return True
        elif self.year % 100 == 0:
            return False
        elif self.year % 4 == 0:
            return True
        else:
            return False

    def year_calc(self):
        self.year = 1970
        while True:
            if self.leap_year():
                if self.stamp_copy - 366 * 24 * 3600 >= 0:
                    self.stamp_copy -= 366 * 24 * 3600
                    self.year += 1
                else:
                    break
            else:
                if self.stamp_copy - 365 * 24 * 3600 >= 0:
                    self.stamp_copy -= 365 * 24 * 3600
                    self.year += 1
                else:
                    break

    def month_calc(self):
        self.month = 1
        if self.leap_year():
            self.month_days[1] = 29
        while True:
            if self.stamp_copy - self.month_days[self.month - 1] * 24 * 3600 >= 0:
                self.stamp_copy -= self.month_days[self.month - 1] * 24 * 3600
                self.month += 1
            else:
                break

    def day_calc(self):
        self.day = 1
        while True:
            if self.stamp_copy - 24 * 3600 >= 0:
                self.stamp_copy -= 24 * 3600
                self.day += 1
            else:
                break

    def hour_calc(self):
        while True:
            if self.stamp_copy - 3600 >= 0:
                self.stamp_copy -= 3600
                self.hour += 1
            else:
                if self.hour > 12:
                    self.hour -= 12
                    self.clock = 'PM'
                break

    def minute_calc(self):
        while True:
            if self.stamp_copy - 60 >= 0:
                self.stamp_copy -= 60
                self.minute += 1
            else:
                break

    def second_calc(self):
        self.second = int(self.stamp_copy)
        if self.second == 60:
            self.second = 0
            self.stamp_copy -= 60
            self.minute += 1

    def sub_second_calc(self):
        self.sub_second = self.stamp_copy - self.second

    def cumulative(self):
        self.reset()
        self.year_calc()
        self.month_calc()
        self.day_calc()
        self.hour_calc()
        self.minute_calc()
        self.second_calc()
        self.sub_second_calc()
        if self.minute < 10:
            self.minute = '0' + str(self.minute)
        return {
            'year': self.year,
            'month': self.month,
            'day': self.day,
            'hour': self.hour,
            'minute': self.minute,
            'second': self.second,
            'sub_second': self.sub_second,
            'day_text': self.days[int((self.stamp // (24 * 3600)) % 7)],
            'month_text': self.months[self.month - 1],
            'clock': self.clock,
            'string': '{hour}:{minute} {clock}, {day_text}, {month_text} {day}, {year}'.format(
                hour=self.hour,
                minute=self.minute,
                clock=self.clock,
                day_text=self.days[int((self.stamp // (24 * 3600)) % 7)],
                month_text=self.months[self.month - 1],
                day=self.day,
                year=self.year
            )
        }


class TimeStamp:
    def __init__(self, form, now):
        self.form = form
        self.calc = TimeForm(now)
        self.out = 0

    def leap_year(self, yr):
        if yr % 400 == 0:
            return True
        elif yr % 100 == 0:
            return False
        elif yr % 4 == 0:
            return True
        else:
            return False

    def convert(self):
        self.out = 0
        for yr in range(1970, int(self.form['year'])):
            if self.leap_year(yr):
                self.out += 366 * 24 * 3600
            else:
                self.out += 365 * 24 * 3600

        for mnth in range(int(self.form['month']) - 1):
            self.out += self.calc.month_days[mnth] * 24 * 3600

        for day in range(0, int(self.form['day']) - 1):
            self.out += 24 * 3600

        if self.form['clock'] == 'PM' and int(self.form['hour']) <= 12:
            self.form['hour'] = int(self.form['hour']) + 12

        for hr in range(0, int(self.form['hour'])):
            self.out += 3600

        for mn in range(0, int(self.form['minute'])):
            self.out += 60

        return self.out
