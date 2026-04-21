Pattern         -   Description                     -   Example

field           -   Single field                    -   name
parent.child    -   Nested field	                -   data.summoner.level
array[]	        -   Array field	                    -   champions[]
array[].field   -   Field in array items	        -   data.champions[].name
{a,b,c}	        -   Multiple fields at same level   -   {name,title,lore}
parent.{a,b}    -   Multiple nested fields	        -   data.summoner.{level,name}
array[].{a,b}   -   Multiple fields in array items  -   data.champions[].{name,title}