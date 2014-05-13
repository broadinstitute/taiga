{% extends "base.tpl" %}

{% macro download_link(format) -%}
  <a href="/rest/v0/datasets/{{meta.dataset_id}}?format={{ format }}">{{ format }}</a>
{%- endmacro %}

{% block title %}Dataset{% endblock %}
{% block content %}
  <h1>
    Name: {{ meta.name }}
  </h1>
  <p> 
    {% if meta.is_published %}
      <span class="badge alert-info">Published</span>
    {% else %}
      <span class="badge alert-danger">Unpublished</span>
    {% endif %}
    </a>
      <form method="POST" action="/dataset/update">
        <input type="hidden" name="pk" value="{{ meta.dataset_id }}">
        <input type="hidden" name="name" value="is_published">
        {% if not meta.is_published %}
          <input type="hidden" name="value" value="True">
          <input type="submit" class="btn" value="Change to 'Published'">
        {% else %}
          <input type="hidden" name="value" value="False">
          <input type="submit" class="btn" value="Change to 'Unpublished'">
        {% endif %}
      </form>
  </p>
  <p>
    Created by {{ meta.created_by }} on {{ meta.created_timestamp }} 
  </p> 
  <p> Versions: 
    {% for version in versions %} 
      {% if version.version == meta.version %}
        <strong>v{{meta.version}}</strong>
      {% else %}
        <a href="/dataset/show/{{ version.dataset_id }}">v{{ version.version }}</a>
      {% endif %}
    {% endfor %}
  </p>
  <p> Download as 
    {{ download_link('hdf5') }} | 
    {{ download_link('gct') }} | 
    {{ download_link('tabular_csv') }} | 
    {{ download_link('tabular_tsv') }} | 
    {{ download_link('csv') }} | 
    {{ download_link('tsv') }}</p>
    
  <p> <a href="/upload/tabular-form?dataset_id={{meta.dataset_id}}">Upload a new version</a> </p>
  <p> Tags: <a href="#" id="tags" data-name="tags" data-type="select2" data-pk="{{meta.dataset_id}}" 
               data-url="/dataset/update" data-title="Enter tags">{{ dataset_tags|join(', ') }}</a></p>
  <p> Data type: <a href="#" id="data_type" data-name="data_type" data-type="select2" 
                  data-pk="{{ meta.dataset_id }}" data-url="/dataset/update" 
                  data-title="Enter data type" data-value="{{ meta.data_type }}">{{ meta.data_type }}</a></p>
  <p> Description: </p>
  <p>
    <a href="#" id="description" data-name="description" data-type="textarea" data-pk="{{ meta.dataset_id }}" 
    data-url="/dataset/update" data-title="Enter description">{{ meta.description }}</a>
  </p>
  
  <h2>Dimensions</h2>
  
  <table class="table table-bordered table-striped">
    <thead>
      <tr>
          <th></th>
          <th>Description</th>
          <th>Values</th>
      </tr>
    </thead>
    
    <tbody>
      {% for dim in dims %}
        <tr>
          <td>{{ loop.index }}</td>
          <td>{{ dim.name }}</td>
          <td>{{ dim.value_count }}</td>
        </tr>
      {% endfor %}
    </tbody>
  </table>

  <h3>Retrieving this dataset within R</h3>
  <p>
    You can fetch this dataset by its ID, and load it into your R session with code below: 
    <pre>dataset &lt;- read.table("{{root_url}}/rest/v0/datasets/{{meta.dataset_id}}?format=tabular_tsv",check.names=F);</pre>

    Fetching the data by it's ID will guarentee you get the same data each and every time this is executed.  Alternatively, you can fetch this data by its name, in in which case, you'll receive the latest version of the data.  Code for fetching by name, is as follows:
    <pre>dataset &lt;- read.table("{{root_url}}/rest/v0/namedDataset?fetch=content&format=tabular_tsv&name={{meta.name|urlencode}}",check.names=F);</pre>
  </p>

{% endblock %}

{% block scripts %}
<script>
  $.fn.editable.defaults.mode = 'inline';
  $(document).ready(function() {
    
    $('.x-editable-class').editable();

    $('#description').editable({
      inputclass: 'input-large',
    });
    
    $('#tags').editable({
      inputclass: 'input-large',
      select2: {
          tags: {{ all_tags_as_json }},
          tokenSeparators: [",", " "]
      }
    });
    
    var autocomplete_if_in_list = function(values) { 
      return function (query){
        var data = {results: []};

        $.each(values, function(){
            if(query.term.length == 0 || this.toUpperCase().indexOf(query.term.toUpperCase()) >= 0 ){
                data.results.push({id: this, text: this });
            }
        });

        if(data.results.length == 0) {
          data.results.push({id: query.term, text: query.term})
        }

        query.callback(data);
      };
    }

    var existing_data_types = {{ existing_data_types }}
    $('#data_type').editable({
      select2: {
        width: 200,
        inputclass: 'input-large',
        query: autocomplete_if_in_list(existing_data_types)
      },
      display: function (value)
      {
          if (!value) {
              $(this).empty();
              return;
          }
          $(this).text(value);
      },
    });
    
  });
</script>
{% endblock %}