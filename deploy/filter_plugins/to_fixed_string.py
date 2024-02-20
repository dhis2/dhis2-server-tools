# filter_plugins/is_float.py
class FilterModule(object):
    def filters(self):
        return {
            'to_fixed_string': self.to_fixed_string,
             'lowercase': self.lowercase,
        }
    def to_fixed_string(self, value):
        if isinstance(value, float):
            return format(value, '.2f')  # Adjust the precision (number of decimal places) as needed
        return str(value)    
    def lowercase(self,value):
        if value is not None and value != 'None':
            return str(value).lower()
        return value
