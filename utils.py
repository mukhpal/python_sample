from rest_framework import serializers

# get file details- file_size, file_type, file_name, file_extenstion 
def get_file_details(file):
    """
    return file  basic detail like- file_size, file_type, file_name, file_extenstion.
    """
    file_size = None
    file_type = None 
    file_name = None 
    file_extenstion = None

    file_size = file.size
    file_type = file.content_type.split("/")[0]
    file_extenstion = file.content_type.split("/")[1]
    file_name = file.name

    return  file_size, file_type, file_name, file_extenstion



class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)
